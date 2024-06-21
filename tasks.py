import os
import time
import json
import boto3
import logging
import asyncio
import instructor
from classes import *
from gpt import *
from format import *
from io import BytesIO
from openai import OpenAI
from htmldocx import HtmlToDocx
from inline import initialize_API
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from ocr import extract_text_from_image
from inline import extract_text_from_file, calculate_cost
import pdb
from datetime import datetime

# Load AWS credentials from environment variables or your configuration management system
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
#S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_BUCKET_NAME = 'smart-resume-hub'

pdb.set_trace()

sse_connections = []
file_statuses = {}

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def update_file_status(filename, status):
    file_statuses[filename] = status
def get_file_status(filename):
    return file_statuses.get(filename, 'not processed')

def download_file_from_s3(filename):
    file_obj = BytesIO()
    s3_client.download_fileobj(S3_BUCKET_NAME, filename, file_obj)
    file_obj.seek(0)
    return file_obj.read()

async def notify_frontend(filename, status):
    event_data = {
        "filename": filename,
        "status": status
    }
    message = f"{json.dumps(event_data)}\n\n"
    for queue in sse_connections:
        await queue.put(message)
    log_debug_info(f"Notify frontend: {message}")


def process_resume(text, filename, flag):
    meta_data = extract_metadata(client, text, filename)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(extract_personal_and_educational_details, client, text, filename, meta_data),
            executor.submit(extract_work_experience, client, text, filename, meta_data),
            executor.submit(extract_licenses_and_certifications, client, text, filename, meta_data)
        ]

        # Wait for all futures to complete
        extraction_results = [future.result() for future in futures]

    pe, work, lc = extraction_results

    elapsed_time = time.time() - start_time

    log_debug_info(f"[F] Detail Extraction took {elapsed_time} for {filename}.")
    log_debug_info(f"[S] Formatting the data!")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(format_personal_details_into_html, pe.pdetail, filename),
            executor.submit(format_educational_details_into_html, pe.edetail, filename),
            executor.submit(format_work_experience_details_into_html, work, flag, filename),
            executor.submit(format_other_details_into_html, lc.licenses, lc.certifications, filename)
        ]

        # Wait for all futures to complete
        formatting_results = [future.result() for future in futures]

    personal_info, educational_info, work_info, other_info = formatting_results

    final_response = format_final_template(personal=personal_info, educational=educational_info, work_experience=work_info, other=other_info, filename=filename)

    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"[F] Formatting file {filename} took {elapsed_time} seconds!")

    new_parser = HtmlToDocx()
    doc = new_parser.parse_html_string(final_response)
    output_stream = BytesIO()
    doc.save(output_stream)

    return final_response.encode('utf-8'), output_stream.getvalue()


def process_each_file(filename, file_type):

    try:
        global client

        client = initialize_API()

        if not client:
            raise RuntimeError("API client initialization failed")

        update_file_status(filename, 'in progress')
        asyncio.run(notify_frontend(filename, 'in progress'))
        
        # Retrieve file from S3

        file_content = download_file_from_s3(filename)

        start_time = time.time()

        text = extract_text_from_file(filename, file_content)

        if "pdf" in filename and len(text) < 20:
            OCR_text = extract_text_from_image(file_content)

            if len(OCR_text) < 20:
                return file_type, f"Processed file: {filename} failed!", (f"{filename.split('.pdf')[0]}-failed.docx", 0)
            else:
                text = OCR_text

        if file_type == 'doctors':
            HTML_bytes, doc_bytes = process_resume(text, filename, True)
        elif file_type == 'nurses':
            HTML_bytes, doc_bytes = process_resume(text, filename, False)

        elapsed_time = time.time() - start_time  # End timing

        log_debug_info(f"[F] Processing file {filename} took {elapsed_time} seconds")

        cost = calculate_cost(text)

        metadata = {
            'name': filename,
            'date': str(datetime.utcnow().isoformat()) + 'Z',
            'status': 'processed',
            'label': 'Resume',
            'cost': str(cost),
            'process_time': str(elapsed_time)
        }
        
        doc_output_filename = f"{filename.split('.pdf')[0]}-done.docx"
        html_output_filename = f"{filename.split('.pdf')[0]}-done.html"
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=doc_output_filename, Body=doc_bytes, Metadata=metadata)
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=html_output_filename, Body=HTML_bytes, Metadata=metadata)


        update_file_status(filename, 'processed')
        asyncio.run(notify_frontend(filename, 'processed'))


    except Exception as e:
        logging.error(f"Error processing file {filename}: {e}", exc_info=True)
        update_file_status(filename, 'error')
        asyncio.run(notify_frontend(filename, 'error'))
