from classes import *
import time

def extract_personal_and_educational_details(client, context, filename, meta_data):
    print(f"Extracting personal and educational details {filename}...")

    prompt = f"""Extract personal and educational details from the following resume,
    Use this information to your advantage for more accurate processing:\n{meta_data.additional_comments}\n
    The field personal details contain {meta_data.personal_details.number_of_items} items and the field is structured in the following way:{meta_data.personal_details.format}.\n{context}
    The field educational details contain {meta_data.educational_details.number_of_items} items and the field is structured in the following way:{meta_data.educational_details.format}.\n{context}"""
    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": prompt}],
        response_model=Personal_Educational,
    )
    
    elapsed_time = time.time() - start_time
    print(f"Extracting personal and educational details took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res

def extract_work_experience(client, context, filename, meta_data):
    prompt = f"""
    Carefully review the entire resume and extract every job experience listed. For each job, include the position title, company name, location, start and end dates, 
    and particularly note the hours worked if mentioned. It's crucial to capture all experiences, from the earliest to the most recent, ensuring no job is omitted.
    Use this information to your advantage for more accurate processing:\n{meta_data.additional_comments}\n
    The field work experience contain {meta_data.work_experience.number_of_items} items and the field is structured in the following way:{meta_data.work_experience.format}.\n{context}
    """
    print(f"Extracting work experience {filename}...")

    start_time = time.time()

    res = client.chat.completions.create_iterable(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt + f"\n{context}"}],
        response_model=WorkExperienceList,
    )

    elapsed_time = time.time() - start_time
    print(f"Extracting work experience took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res


def extract_licenses_and_certifications(client, context, filename, meta_data):

    print(f"Extracting licenses and certifications {filename}...")

    prompt = f"""Extract licences and certifications from the following resume,
    Use this information to your advantage for more accurate processing:\n{meta_data.additional_comments}\n
    The field licenses contain {meta_data.licenses.number_of_items} items and the field is structured in the following way:{meta_data.licenses.format}.\n{context}
    The field certifications contain {meta_data.certifications.number_of_items} items and the field is structured in the following way:{meta_data.certifications.format}.\n{context}"""

    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": prompt}],
        response_model=License_Certification,
    )

    elapsed_time = time.time() - start_time
    print(f"Extracting licenses and certifications took {elapsed_time} seconds for {filename} | start_time:{start_time}")

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
    Resume:\n{context}"""
 
    print(f"pre-processing {filename}...")

    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": prompt}],
        response_model=ResumeMetadata,
    )
    elapsed_time = time.time() - start_time
    print(f"Extracting ResumeMetadata took {elapsed_time} seconds for {filename} | start_time:{start_time}")

    return res

