import json
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from botocore.exceptions import NoCredentialsError
import os
from openai import OpenAI
import instructor

app = FastAPI()

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

def log_debug_info(message):
    # Placeholder for your logging function
    print(message)

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
