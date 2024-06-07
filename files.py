import time
import concurrent.futures
from io import BytesIO
from htmldocx import HtmlToDocx
from gpt import *
from utils import *
from ocr import *
from inline import calculate_cost
import asyncio
from g_lobal import *
from celery import group
from inline import download_file_from_s3

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

def process_resume(client, text, filename, flag):

    meta_data = extract_metadata(client, text, filename)

    start_time = time.time()

    extraction_group = group(
        extract_personal_and_educational_details.s(client, text, filename, meta_data),
        extract_work_experience.s(client, text, filename, meta_data),
        extract_licenses_and_certifications.s(client, text, filename, meta_data)
    )

    results = extraction_group().get()  # Blocking call to get the results

    pe, work, lc = results
    
    elapsed_time = time.time() - start_time

    log_debug_info(f"[F] Detail Extraction took {elapsed_time} for {filename}.")
    log_debug_info(f"[S] Formatting the data!")

    personal = pe.pdetail
    educational = pe.edetail
    licenses = lc.licenses
    certification = lc.certifications

    start_time = time.time()
    
    formatting_group = group(
        format_personal_details_into_html.s(personal, filename),
        format_educational_details_into_html.s(educational, filename),
        format_work_experience_details_into_html.s(work, flag, filename),
        format_other_details_into_html.s(licenses, certification, filename)
    )

    formatted_results = formatting_group().get()  # Blocking call to get the results

    personal_info, educational_info, work_info, other_info = formatted_results

    final_response = format_final_template(personal=personal_info, educational=educational_info, work_experience=work_info, other=other_info, filename=filename)
    #final_html = get_final_html(final_response).replace('```html', '').replace('```', '')

    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"[F] Formating file {filename} took {elapsed_time} seconds!")

    new_parser = HtmlToDocx()
    doc = new_parser.parse_html_string(final_response)
    output_stream = BytesIO()
    doc.save(output_stream)

    return output_stream.getvalue()

@Capp.task
def process_each_file(filename, file_type):
    start_time = time.time()

    # Retrieve file from S3
    file_content = download_file_from_s3(filename)

    text = extract_text_from_file(filename, file_content)

    text = extract_text_from_file(filename, file_content)

    if "pdf" in filename and len(text) < 20:
        
        OCR_text = extract_text_from_image(file_content)

        if len(OCR_text) < 20:
            return type, f"Processed file: {filename} failed!", (f"{filename.split('.pdf')[0]}-failed.docx", 0)
        else:
            text = OCR_text

    if file_type == 'doctors':
        doc_bytes = process_resume(client, text, filename, True)
    elif file_type == 'nurses':
        doc_bytes = process_resume(client, text, filename, False)

    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"[F] Processing file {filename} took {elapsed_time} seconds")

    cost = calculate_cost(text)

    asyncio.run(notify_frontend(filename, file_type, 'processed'))

    return file_type, f"Processed file: {filename}", (f"{filename.split('.pdf')[0]}-done.docx", doc_bytes), cost