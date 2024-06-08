import concurrent.futures
from fastapi import FastAPI
from classes import log_debug_info
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi import HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.requests import Request
import tempfile
from pydantic import BaseModel
from botocore.exceptions import NoCredentialsError
from tasks import process_each_file, sse_connections, s3_client, S3_BUCKET_NAME
import logging

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

@app.post("/api/process")
async def process_file(file: UploadFile = File(...), file_type: str = Form(...)):
    log_debug_info(f"[*] Received file: {file.filename} with type: {file_type}")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_each_file, file.filename, file_type)
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

# Register the startup event
app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
