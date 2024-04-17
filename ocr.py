import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def extract_text_from_image(pdf_path):
    # Convert PDF to a list of images
    images = convert_from_path(pdf_path, 300)  # 300 dpi is a good standard for image quality

    text = ""
    for img in images:
        # Use pytesseract to do OCR on the converted image
        text += pytesseract.image_to_string(img)
    
    return text
