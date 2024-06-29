from tasks import process_each_file, sse_connections, s3_client, S3_BUCKET_NAME, get_file_status
from fastapi import HTTPException, File, UploadFile, FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import NoCredentialsError, ClientError
from sse_starlette.sse import EventSourceResponse
from fastapi.requests import Request
from classes import log_debug_info 
from pydantic import BaseModel
from many_to_one import process_many_to_one
import concurrent.futures
import tempfile
import asyncio
from datetime import datetime
from format import generate_missing_info_email


# from auth import authenticate_user, create_access_token, Token, get_current_active_user, User
# from auth_utils import ACCESS_TOKEN_EXPIRE_MINUTES
from classes import log_debug_info

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
# @app.post("/token", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):

#     fake_users_db = {
#         "johndoe": {
#             "username": "johndoe",
#             "hashed_password": "$2b$12$KIXx0hXbGZlqX8kzC3AIuOkW6ILuKqkCQHlfzT9zCH5M2.lAF0vH6",  # "secret"
#         }
#     }

#     user = authenticate_user(fake_users_db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/users/me/", response_model=User)
# async def read_users_me(current_user: User = Depends(get_current_active_user)):
#     return current_user

@app.post("/api/process/{filename}")
async def process_file(filename: str):
    log_debug_info(f"[*] Received file: {filename} with type")#: {file_type}")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_each_file, filename, 'doctors', 'test')
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
        metadata = {
            'name': file.filename,
            'date': datetime.utcnow().isoformat() + 'Z',  # Current date and time in ISO format
            'status': 'uploaded',
        }
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file.filename, Body=file.file, Metadata=metadata)
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

class FileMetadata(BaseModel):
    name: str
    date: str
    status: str
    label: str
    pages: str

@app.get("/api/files", response_model=list[FileMetadata])
async def get_files():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        files = []

        if 'Contents' in response:
            for obj in response['Contents']:
                # Assume metadata is stored in a specific format in S3
                metadata = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])
                file_metadata = {
                    "name": obj['Key'],
                    "date": obj['LastModified'].isoformat(),
                    "status": metadata.get('Metadata', {}).get('status', 'unknown'),
                    "label": metadata.get('Metadata', {}).get('label', 'unknown'),
                    "pages": metadata.get('Metadata', {}).get('pages', 'unknown'),
                }
                files.append(file_metadata)

        return files
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vaccination")
async def many_to_one_vaccination(files: list[str]):
    log_debug_info(f"[*] Received vaccination files: {files}")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_many_to_one, files, 'Vaccination Record', 'test')
    return {"message": "Vaccination processing started successfully"}

@app.post("/api/certification")
async def many_to_one_certification(files: list[str]):
    log_debug_info(f"[*] Received certification files: {files}")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_many_to_one, files, 'Certification', 'test')
    return {"message": "Certification processing started successfully"}

@app.post("/api/generate-email")
async def generate_missing_info_email_endpoint(data: dict):
    sections_missing = data.get("sections_missing", [])
    description = data.get("description", "")
    log_debug_info(f"[*] Generating email with sections: {sections_missing} and description: {description}")
    email_content = generate_missing_info_email(sections_missing, description)
    return {"emailContent": email_content}

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



