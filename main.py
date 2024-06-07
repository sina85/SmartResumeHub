import json
from openai import OpenAI
import instructor
from classes import log_debug_info
from g_lobal import *
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
import asyncio
from fastapi import HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.requests import Request
import tempfile
from pydantic import BaseModel
from botocore.exceptions import NoCredentialsError
from files import process_each_file
import pdb

app = FastAPI()

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

# Load AWS credentials from environment variables or your configuration management system
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
#S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_BUCKET_NAME = 'smart-resume-hub'

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


@app.post("/api/process")
async def process_file(file: UploadFile = File(...), file_type: str = Form(...)):
    process_each_file.delay(file.filename, file_type)
    return {"message": "Processing started"}


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

@app.get("/")
async def read_root():
    return {"Hello": "World"}


async def startup_event():
    log_debug_info('[I] Starting Application...')

    api_key = ''
    config_path = 'config.json'

    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
            api_key = config.get('api_key', '')

        if not api_key:
            error_message = 'API key not found in the configuration file.'
            log_debug_info(f'[E] {error_message}')

        client = OpenAI(api_key=api_key)
        client = instructor.from_openai(client)
        log_debug_info('[I] API key loaded successfully.')

    except FileNotFoundError:
        error_message = 'Configuration file not found.'
        log_debug_info(f'[E] {error_message}')

    except json.JSONDecodeError:
        error_message = 'Invalid JSON format in the configuration file.'
        log_debug_info(f'[E] {error_message}')

    except Exception as e:
        error_message = f'An error occurred while loading the API key: {str(e)}'
        log_debug_info(f'[E] {error_message}')

# Register the startup event
app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
