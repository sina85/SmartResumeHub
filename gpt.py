from classes import *
import time
from inline import extract_text_from_file
import base64
from inline import encode_image, optimize_image
import fitz
from io import BytesIO
from g_lobal import Capp

@Capp.task
def extract_personal_and_educational_details(client, context, filename, meta_data):
    log_debug_info(f"[S] Extracting personal and educational details {filename}...")

    prompt = f"""Extract personal and educational details from the following resume,
    Use this information to your advantage for more accurate processing:\n{meta_data.additional_comments}\n
    The field personal details contain {meta_data.personal_details.number_of_items} items and the field is structured in the following way:{meta_data.personal_details.format}.\n
    The field educational details contain {meta_data.educational_details.number_of_items} items and the field is structured in the following way:{meta_data.educational_details.format}\n\"\"\"{context}\"\"\""""
    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        response_model=Personal_Educational,
    )
    
    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Extracting personal and educational details took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res

@Capp.task
def extract_work_experience(client, context, filename, meta_data):
    prompt = f"""
    Carefully review the entire resume and extract every job experience listed. For each job, include the position title, company name, location, start and end dates, 
    and particularly note the hours worked if mentioned. It's crucial to capture all experiences, from the earliest to the most recent, ensuring no job is omitted.
    Use this information to your advantage for more accurate processing:\n{meta_data.additional_comments}\n
    The field work experience contain {meta_data.work_experience.number_of_items} items and the field is structured in the following way:{meta_data.work_experience.format}\n\"\"\"{context}\"\"\""""
    log_debug_info(f"[S] Extracting work experience {filename}...")

    start_time = time.time()

    res = client.chat.completions.create_iterable(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        response_model=WorkExperienceList,
    )

    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Extracting work experience took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res

@Capp.task
def extract_licenses_and_certifications(client, context, filename, meta_data):

    log_debug_info(f"[S] Extracting licenses and certifications {filename}...")

    prompt = f"""Extract licences and certifications from the following resume,
    Use this information to your advantage for more accurate processing:\n{meta_data.additional_comments}\n
    The field licenses contain {meta_data.licenses.number_of_items} items and the field is structured in the following way:{meta_data.licenses.format}\n
    The field certifications contain {meta_data.certifications.number_of_items} items and the field is structured in the following way:{meta_data.certifications.format}\n\"\"\"{context}\"\"\""""

    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        response_model=License_Certification,
    )

    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Extracting licenses and certifications took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res


def extract_metadata(client, context, filename):
    prompt = f"""Please review the following resume carefully and provide a detailed report covering the following aspects:
    Do this for each section:
    - Indicate whether this section is present in the resume or not.
    - If present, comment on the format or structure of the this section. Provide any additional comments, observations, or potential issues you notice in the resume that could be relevant for accurate data extraction in the subsequent step.
    - Provide the number of items included in this section and some examples of these items.
    These sections are ->
    1. Personal Details Section 
    2. Educational Details Section
    3. Work Experience Section
    4. Certifications Section
    5. Licenses Section
    \n\"\"\"{context}\"\"\""""
 
    log_debug_info(f"[S] Pre-processing {filename}...")

    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        response_model=ResumeMetadata,
    )
    elapsed_time = time.time() - start_time
    log_debug_info(f"[D] Extracting ResumeMetadata took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res


def classify_type_many_to_one(client, file):
    filename, file_content = file.name, file.getvalue()
    text = extract_text_from_file(filename, file_content)

    prompt = f"Classify the following document as either 'Certification' or 'Vaccination Record'. It is important that you only respond with either of these options and nothing else."

    if len(text) > 20:
        prompt += f"\n\n{text}"
        messages_list = [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }]

    else:
        # Convert file content to base64 for image classification
        doc = fitz.open(stream=file_content, filetype="pdf")

        # Render the first page to an image
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)  # Set DPI according to desired resolution

        # Convert pixmap to a BytesIO object
        image_bytes = BytesIO(pix.tobytes("png"))
        base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')


        images_content = [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}}]

        messages_list = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + images_content
        }]

    log_debug_info(f'[$] classifying many to one {filename}')

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages_list,
        temperature=0,
        max_tokens=100,
        response_model=Classify_many_to_one,
    )

    return response.class_type

def extract_certification_info(client, image_bytes, filename):
    optimized_image_bytes = optimize_image(image_bytes)

    base64_image = encode_image(optimized_image_bytes)
    
    prompt = f"""
    Extract the following information from the certification document:
    - Name of the person
    - Type of certification
    - Issue date
    - Expiration date
    
    This is a scanned image and might contain handwritten annotations.
    If there is missing information please respond with Not Specified.
    There may be multiple certifications or one."""

    images_content = [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}]

    messages_list = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt}
        ] + images_content
    }]

    log_debug_info(f"[$] Calling API to extract certification info for {filename}...")

    start_time = time.time()

    response, completion = client.chat.completions.create_with_completion(
        model="gpt-4o",
        messages=messages_list,
        temperature=0,
        response_model=Certification_Many_to_One_List,
        logprobs=True,  # request log probabilities for all tokens
        top_logprobs=5
    )

    #pdb.set_trace()

    elapsed_time = time.time() - start_time
    log_debug_info(f"[#] Certification Extraction complete for {filename} | elapsed_time {elapsed_time}")

    return response

def extract_vaccination_info(client, image_path, filename):
    optimized_image_path = optimize_image(image_path)

    base64_image = encode_image(optimized_image_path)
    
    prompt = f"""
    Extract Vaccination/Immunization records from this document:
    - Name of Vaccination
    - Date of Vaccination
    - Name of the person
    - Whether this person had a religious exemption
    This is a scanned image and might contain handwritten annotations.
    If there is missing infomration please respond with Not Specified."""
    
    images_content = [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}}]

    messages_list = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt}
        ] + images_content
    }]

    log_debug_info(f"[$] Extracting vaccination info from {filename}...")

    start_time = time.time()

    res, completion = client.chat.completions.create_with_completion(
        model="gpt-4o",
        messages=messages_list,
        temperature=0,
        response_model=ImmunizationRecord_Many_to_One_List,
        logprobs=True,  # request log probabilities for all tokens
        top_logprobs=5
    )
    
    #pdb.set_trace()

    elapsed_time = time.time() - start_time
    log_debug_info(f"[#] Extraction complete for {filename} | elapsed_time {elapsed_time}")
    
    return res