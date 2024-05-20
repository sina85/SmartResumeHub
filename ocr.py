import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

def convert_to_black_and_white(image_path, output_path):
    """
    Convert an image to black and white and save it.
    Args:
    image_path (str): The path to the image file.
    output_path (str): The path where the black and white image will be saved.
    """
    with Image.open(image_path) as img:
        bw = img.convert('1')  # '1' for a binary image (black and white)
        bw.save(output_path)

# Example usage:
#convert_to_black_and_white('path/to/color/image.png', 'path/to/bw/image.png')


def extract_text_from_image(pdf_content):
    # Convert PDF to a list of images
    images = convert_from_bytes(pdf_content, 300)  # 300 dpi is a good standard for image quality

    text = ""
    for img in images:
        # Use pytesseract to do OCR on the converted image
        text += pytesseract.image_to_string(img)
    
    return text