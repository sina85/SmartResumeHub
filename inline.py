from PyPDF2 import PdfReader, PdfWriter
import docx2txt
import zipfile
import tempfile
from pdfminer.high_level import extract_text
from io import BytesIO
import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import base64
import tiktoken
import subprocess
import boto3
import os

Image.MAX_IMAGE_PIXELS = None


AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = 'smart-resume-hub'

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='your_region'
)

def download_file_from_s3(filename):
    file_obj = BytesIO()
    s3_client.download_fileobj(S3_BUCKET_NAME, filename, file_obj)
    file_obj.seek(0)
    return file_obj.read()

def optimize_image(image_bytes, format='JPEG'):
    """
    Optimize the image.
    Args:
    image_bytes (BytesIO): The image file in bytes.
    format (str): The format to save the optimized image in.
    
    Returns:
    BytesIO: The optimized image in bytes.
    """
    
    max_size = (1024, 1024)
    output_bytes = BytesIO()

    image = Image.open(image_bytes)
    
    if format == 'WEBP':
        image.save(output_bytes, "WEBP", quality=100)
    elif format == 'PNG':
        with BytesIO() as temp_bytes:
            image.save(temp_bytes, "PNG")
            temp_bytes.seek(0)
            subprocess.run(['optipng', '-o2', '-out', '-', '-'], input=temp_bytes.read(), stdout=output_bytes)
    else:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(output_bytes, "JPEG", quality=85)

    output_bytes.seek(0)
    return output_bytes

def encode_image(image_bytes):
    """
    Encode the image to base64.
    Args:
    image_bytes (BytesIO): The image file in bytes.
    
    Returns:
    str: The base64 encoded image.
    """
    return base64.b64encode(image_bytes.getvalue()).decode('utf-8')

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
        return extract_text_from_docx(BytesIO(file_content))
    else:
        raise ValueError("Unsupported file format")

def download_processed_files(processed_files, type):
    zip_buffer = BytesIO()
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

def remove_metadata(input_pdf, output_pdf):
    """
    Removes metadata from a PDF file.
    Args:
    input_pdf (str): The path to the input PDF file.
    output_pdf (str): The path to the output PDF file without metadata.
    """
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open(output_pdf, 'wb') as out:
        writer.write(out)

# Example usage:
# remove_metadata('path/to/your/file.pdf', 'path/to/output/file.pdf')

def compress_pdf_mupdf(input_path, output_path, quality=50):
    """
    Compresses a PDF by reducing image quality within the document.
    Args:
    input_path (str): Path to the input PDF.
    output_path (str): Path to the output compressed PDF.
    quality (int): JPEG quality for image compression.
    """
    doc = fitz.open(input_path)
    for page in doc:
        image_list = page.get_images(full=True)
        for img in image_list:
            xref = img[0]
            img_info = page.get_image_info(xref)  # Get detailed image information
            bbox = fitz.Rect(img_info["from"])  # Correct extraction of bbox from image info
            base_image = doc.extract_image(xref)
            img = Image.open(BytesIO(base_image["image"]))
            img_io = BytesIO()
            img.convert('RGB').save(img_io, "JPEG", quality=quality)
            img_data = img_io.getvalue()
            page.insert_image(bbox, stream=img_data, keep_proportion=True, overlay=True)

    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

# Example usage:
# compress_pdf_mupdf('path/to/original.pdf', 'path/to/compressed.pdf', quality=40)

def count_tokens(input_string: str) -> int:
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(input_string)
    return len(tokens)

def calculate_cost(input_string: str, cost_per_million_tokens: float = 5) -> float:
    num_tokens = count_tokens(input_string)
    total_cost = (num_tokens / 1_000_000) * cost_per_million_tokens
    return total_cost
