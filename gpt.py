from classes import *
import time

def extract_personal_details(client, context):
    print('Extracting personal details...')
    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": f"Extract personal details from the following resume:\n{context}"}],
        response_model=PersonalDetails,
    )
    
    elapsed_time = time.time() - start_time
    print(f"Extracting personal details took {elapsed_time} seconds | {start_time}")

    return res

def extract_education_details(client, context):
    print('Extracting educational details...')
    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": f"Extract education details from the following resume:\n{context}"}],
        response_model=EducationList,
    )

    elapsed_time = time.time() - start_time
    print(f"Extracting educational details took {elapsed_time} seconds | {start_time}")

    return res

def extract_work_experience(client, context):
    prompt = """
    Carefully review the entire resume and extract every job experience listed. For each job, include the position title, company name, location, start and end dates, 
    and particularly note the hours worked if mentioned. It's crucial to capture all experiences, from the earliest to the most recent, ensuring no job is omitted.
    """
    print('Extracting work experience...')

    start_time = time.time()

    res = client.chat.completions.create_iterable(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt + f"\n{context}"}],
        response_model=WorkExperienceList,
    )

    elapsed_time = time.time() - start_time
    print(f"Extracting work experience took {elapsed_time} seconds | {start_time}")

    return res


def extract_all_licenses(client, context):

    print('Extracting all licenses...')
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": f"Extract all licenses from the following resume:\n{context}"}],
        response_model=LicenseList,
    )

    elapsed_time = time.time() - start_time
    print(f"Extracting all licenses took {elapsed_time} seconds | {start_time}")

    return res


def extract_all_certifications(client, context):

    print('Extracting all certifications...')
    
    start_time = time.time()

    res = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=.1,
        messages=[{"role": "user", "content": f"Extract all certifications from the following resume:\n{context}"}],
        response_model=CertificationList,
    )
    elapsed_time = time.time() - start_time
    print(f"Extracting all certifications took {elapsed_time} seconds | {start_time}")

    return res
