import time
import io
import docx2txt
import zipfile
import tempfile
import concurrent.futures
from pdfminer.high_level import extract_text
from docx import Document
from gpt import *
import streamlit as st
from ocr import *
import pdb


def extract_text_from_pdf(pdf_file):
    return extract_text(pdf_file)

def extract_text_from_docx(docx_file):
    return docx2txt.process(docx_file)

def extract_text_from_file(filename, file_content):
    if filename.lower().endswith('.pdf'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_content)
            return extract_text_from_pdf(tmp_file.name)
    elif filename.lower().endswith('.docx'):
        return extract_text_from_docx(io.BytesIO(file_content))
    else:
        raise ValueError("Unsupported file format")
    

def process_resume(client, text, filename, flag):

    meta_data = extract_metadata(client, text, filename)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        future_pe = executor.submit(extract_personal_and_educational_details, client, text, filename, meta_data)
        future_work = executor.submit(extract_work_experience, client, text, filename, meta_data)
        future_lc = executor.submit(extract_licenses_and_certifications, client, text, filename, meta_data)

        # Await the results of the futures
        pe = future_pe.result()
        work = future_work.result()
        lc = future_lc.result()

    log_debug_info(f"Detail Extraction Finished! Formatting the data for {filename}")

    personal = pe.pdetail
    educational = pe.edetail
    licenses = lc.licenses
    certification = lc.certifications

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        fpersonal_info = executor.submit(format_personal_details_into_html, personal)
        feducational_info = executor.submit(format_educational_details_into_html, educational)
        fwork_info = executor.submit(format_work_experience_details_into_html, work, flag)
        fother_info = executor.submit(format_other_details_into_html, licenses, certification)

        personal_info = fpersonal_info.result()
        educational_info = feducational_info.result()
        work_info = fwork_info.result()
        other_info = fother_info.result()

    final_response = format_final_template(personal=personal_info, educational=educational_info, work_experience=work_info, other=other_info)
    final_html = get_final_html(final_response).replace('```html', '').replace('```', '')

    document = Document()
    sec = document.AddSection()
    paragraph = sec.AddParagraph()
    paragraph.AppendHTML(final_html)

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
        document.SaveToFile(temp_file.name, FileFormat.Docx2019)
        with open(temp_file.name, 'rb') as temp_file_read:
            doc_bytes = temp_file_read.read()
    
    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"Formating file {filename} took {elapsed_time} seconds")

    return doc_bytes

def process_each_file(client, all_files):
    start_time = time.time()  # Start timing

    file, type = all_files

    filename, file_content = file.name, file.getvalue()

    text = extract_text_from_file(filename, file_content)

    if "pdf" in filename and len(text) < 20:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resume_dir = os.path.join(current_dir, 'Resume_Sample')
        full_path = os.path.join(resume_dir, filename)
        OCR_text = extract_text_from_image(full_path)
        if len(OCR_text) < 20:
            return type, f"Processed file: {filename} failed!", (f"{filename.split('.pdf')[0]}-failed.docx", 0)
        else:
            text = OCR_text

    if type == 'doctors':
        doc_bytes = process_resume(client, text, filename, True)
    elif type == 'nurses':    
        doc_bytes = process_resume(client, text, filename, False)

    elapsed_time = time.time() - start_time  # End timing

    log_debug_info(f"Processing files took {elapsed_time} seconds")

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

def download_processed_files(processed_files, type):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, file_data in processed_files:
            zip_file.writestr(file_name, file_data)
    zip_buffer.seek(0)
    st.download_button(
        label=f"Download Processed {type.capitalize()} Files as ZIP",
        data=zip_buffer,
        file_name=f"processed_{type}_resumes.zip",
        mime="application/zip",
        key=f"download_{type}"
    )