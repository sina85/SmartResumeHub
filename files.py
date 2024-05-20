import time
import concurrent.futures
from io import BytesIO
import streamlit as st
from htmldocx import HtmlToDocx
from gpt import *
from utils import *
from ocr import *

def process_resume(client, text, filename, flag):

    meta_data = extract_metadata(client, text, filename)

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        future_pe = executor.submit(extract_personal_and_educational_details, client, text, filename, meta_data)
        future_work = executor.submit(extract_work_experience, client, text, filename, meta_data)
        future_lc = executor.submit(extract_licenses_and_certifications, client, text, filename, meta_data)

        # Await the results of the futures
        pe = future_pe.result()
        work = future_work.result()
        lc = future_lc.result()
    
    elapsed_time = time.time() - start_time

    log_debug_info(f"[F] Detail Extraction took {elapsed_time} for {filename}.")
    log_debug_info(f"[S] Formatting the data!")

    personal = pe.pdetail
    educational = pe.edetail
    licenses = lc.licenses
    certification = lc.certifications

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        fpersonal_info = executor.submit(format_personal_details_into_html, personal, filename)
        feducational_info = executor.submit(format_educational_details_into_html, educational, filename)
        fwork_info = executor.submit(format_work_experience_details_into_html, work, flag, filename)
        fother_info = executor.submit(format_other_details_into_html, licenses, certification, filename)

        personal_info = fpersonal_info.result()
        educational_info = feducational_info.result()
        work_info = fwork_info.result()
        other_info = fother_info.result()

    final_response = format_final_template(personal=personal_info, educational=educational_info, work_experience=work_info, other=other_info, filename=filename)
    #final_html = get_final_html(final_response).replace('```html', '').replace('```', '')

    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"[F] Formating file {filename} took {elapsed_time} seconds!")

    new_parser = HtmlToDocx()
    doc = new_parser.parse_html_string(final_response)
    output_stream = BytesIO()
    doc.save(output_stream)

    return output_stream.getvalue()

def process_each_file(client, all_files):
    start_time = time.time()  # Start timing

    file, type = all_files

    filename, file_content = file.name, file.getvalue()

    text = extract_text_from_file(filename, file_content)

    if "pdf" in filename and len(text) < 20:
        
        OCR_text = extract_text_from_image(file_content)

        if len(OCR_text) < 20:
            return type, f"Processed file: {filename} failed!", (f"{filename.split('.pdf')[0]}-failed.docx", 0)
        else:
            text = OCR_text

    if type == 'doctors':
        doc_bytes = process_resume(client, text, filename, True)
    elif type == 'nurses':    
        doc_bytes = process_resume(client, text, filename, False)

    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"[F] Processing file {filename} took {elapsed_time} seconds")

    return type, f"Processed file: {filename}", (f"{filename.split('.pdf')[0]}-done.docx", doc_bytes)

def process_files(client, uploaded_files_doctors, uploaded_files_nurses):

    doctor_files = [(file, 'doctors') for file in uploaded_files_doctors]
    nurse_files = [(file, 'nurses') for file in uploaded_files_nurses]
    all_files = doctor_files + nurse_files

    processed_files_dr = []
    processed_files_nr = []

    with st.spinner(f'Processing files...'):
        max_processes = 3
        with concurrent.futures.ThreadPoolExecutor(max_processes) as executor:
            results = executor.map(lambda file_info: process_each_file(client, file_info), all_files)
        for type, message, processed_file in results:
            if type == 'doctors' and processed_file:
                processed_files_dr.append(processed_file)
                st.success(message)
            elif type == 'doctors':
                st.error(message)
            if type == 'nurses' and processed_file:
                processed_files_nr.append(processed_file)
                st.success(message)
            elif type == 'nurses':
                st.error(message)

    return processed_files_dr, processed_files_nr