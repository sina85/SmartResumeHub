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
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from ocr import extract_text_from_image
from inline import extract_text_from_file, calculate_cost
import pdb

# Load AWS credentials from environment variables or your configuration management system
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
#S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_BUCKET_NAME = 'smart-resume-hub'

api_key = ''
config_path = 'config.json'
sse_connections = []

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def download_file_from_s3(filename):
    file_obj = BytesIO()
    s3_client.download_fileobj(S3_BUCKET_NAME, filename, file_obj)
    file_obj.seek(0)
    return file_obj.read()

async def notify_frontend(filename, file_type, status):
    for connection in sse_connections:
        await connection.put({
            "event": "file_processed",
            "data": {
                "filename": filename,
                "file_type": file_type,
                "status": status
            }
        })

def initialize_API():
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

        # Return a dictionary representation of the instructor_client if needed
        return client
    except FileNotFoundError:
        error_message = 'Configuration file not found.'
        log_debug_info(f'[E] {error_message}')

    except json.JSONDecodeError:
        error_message = 'Invalid JSON format in the configuration file.'
        log_debug_info(f'[E] {error_message}')

    except Exception as e:
        error_message = f'An error occurred while loading the API key: {str(e)}'
        log_debug_info(f'[E] {error_message}')
    
    return None

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

    return output_stream.getvalue()


def process_each_file(filename, file_type):

    try:
        global client

        client = initialize_API()

        if not client:
            raise RuntimeError("API client initialization failed")

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
            doc_bytes = process_resume(text, filename, True)
        elif file_type == 'nurses':
            doc_bytes = process_resume(text, filename, False)

        elapsed_time = time.time() - start_time  # End timing

        log_debug_info(f"[F] Processing file {filename} took {elapsed_time} seconds")

        cost = calculate_cost(text)
        
        output_filename = f"{filename.split('.pdf')[0]}-done.docx"
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=output_filename, Body=doc_bytes)

        asyncio.run(notify_frontend(filename, file_type, 'processed'))

    except Exception as e:
        logging.error(f"Error processing file {filename}: {e}", exc_info=True)