from tasks import process_each_file, sse_connections, s3_client, S3_BUCKET_NAME, get_file_status
from fastapi import HTTPException, File, UploadFile, Form, FastAPI, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import NoCredentialsError
from sse_starlette.sse import EventSourceResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dependencies import get_current_user
from models import UserCredits
from classes import log_debug_info 
from pydantic import BaseModel
from psql import get_db
from schemas import CreateCheckoutSessionRequest
import concurrent.futures
import tempfile
import asyncio
from models import UserCredits, User
import stripe
import json

app = FastAPI()

executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)

class PresignedUrlRequest(BaseModel):
    fileName: str
    fileType: str

# Add CORS middleware
origins = [
    "http://localhost:3000",  # React front-end
    "http://127.0.0.1:3000",  # React front-end
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def initialize_stripe():
    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
            stripe_secret_key = config.get('stripe_secret_key', '')

        if not stripe_secret_key:
            error_message = 'stripe_secret_key not found in the configuration file.'
            log_debug_info(f'[E] {error_message}')

        stripe.api_key = stripe_secret_key

        log_debug_info('[I] stripe_secret_key loaded successfully.')

    except FileNotFoundError:
        error_message = 'Configuration file not found.'
        log_debug_info(f'[E] {error_message}')

    except json.JSONDecodeError:
        error_message = 'Invalid JSON format in the configuration file.'
        log_debug_info(f'[E] {error_message}')

    except Exception as e:
        error_message = f'An error occurred while loading the stripe_secret_key: {str(e)}'
        log_debug_info(f'[E] {error_message}')
    
    return None

@app.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = 'whsec_...'  # webhook secret

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Retrieve the session and update user credits
        user_id = session['client_reference_id']
        credits_purchased = session['metadata']['credits']

        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits += int(credits_purchased)
            db.commit()

            # Notify the front-end (implement as needed)

    return {"status": "success"}

@app.post("/api/create-checkout-session")
def create_checkout_session(request: CreateCheckoutSessionRequest, db: Session = Depends(get_db)):
    try:
        log_debug_info(f"Received request data: {request}")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{request.credits} File Processing Credits",
                    },
                    "unit_amount": request.amount,  # Amount in cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        return {"id": session.id}
    except Exception as e:
        log_debug_info(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/credits/balance")
async def get_credits_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        log_debug_info(f"Fetching credits for user_id: {user_id}")
        result = await db.execute(
            text("SELECT credits FROM users WHERE id = :user_id"), {"user_id": user_id}
        )
        user = result.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"credits": user.credits}
    except Exception as e:
        log_debug_info(f"Error fetching credits balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_file(file: UploadFile = File(...), file_type: str = Form(...)):
    log_debug_info(f"[*] Received file: {file.filename} with type: {file_type}")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_each_file, file.filename, file_type)
    return {"message": "Processing started"}

@app.get("/api/file-status/{filename}")
async def get_file_status_endpoint(filename: str):
    status = get_file_status(filename)
    return {"filename": filename, "status": status}

@app.get("/api/events")
async def sse_endpoint(request: Request):
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections.append(queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                log_debug_info(f"Event generated: {event}")
                yield event
        finally:
            sse_connections.remove(queue)

    return EventSourceResponse(event_generator())

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, file.filename)
        file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
        return {"fileUrl": file_url}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fetch/{filename}")
async def fetch_file(filename: str):
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            s3_client.download_fileobj(S3_BUCKET_NAME, filename, tmp)
            tmp.seek(0)
            return FileResponse(tmp.name, filename=filename)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fetch-html/{filename}")
async def fetch_file_as_html(filename: str):
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            s3_client.download_fileobj(S3_BUCKET_NAME, filename, tmp)
            tmp.seek(0)
            html_content = tmp.read().decode('utf-8')
            return HTMLResponse(content=html_content)
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return {"Hello": "World"}


async def startup_event():
    log_debug_info('[I] Starting Application...')

# Register the startup event
app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



