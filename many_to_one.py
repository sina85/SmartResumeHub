import fitz
from classes import log_debug_info
from io import BytesIO
from inline import initialize_API 
from gpt import classify_type_many_to_one, extract_certification_info, extract_vaccination_info
from classes import ImmunizationRecord_Many_to_One, Certification_Many_to_One_List
import json
import concurrent
from datetime import datetime
from main import s3_client, S3_BUCKET_NAME

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImmunizationRecord_Many_to_One) or isinstance(obj, Certification_Many_to_One_List):
            return obj.model_dump()
        return super().default(obj)

def custom_decoder(dct):
    if 'type' in dct and 'date' in dct:
        return ImmunizationRecord_Many_to_One(**dct)
    if 'name' in dct and 'certifications' in dct:
        return Certification_Many_to_One_List(**dct)
    return dct

def dump_data_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, cls=CustomEncoder, indent=4)

def load_data_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f, object_hook=custom_decoder)

def download_file_from_s3(filename):
    file_obj = BytesIO()
    s3_client.download_fileobj(S3_BUCKET_NAME, filename, file_obj)
    file_obj.seek(0)
    return file_obj.read()

def process_many_to_one(list_of_file_names, classification, user_id):

    client = initialize_API()

    vaccine_consolidated_records = []
    certification_consolidated_records = []

    def process__file(filename):
        nonlocal classification
        file_content = download_file_from_s3(filename)

        log_debug_info(f'[$] Processing many to one {filename}')

        if classification == 'Unknown':
            classification = classify_type_many_to_one(client, file_content)
        
        if classification == 'Vaccination Record':
            log_debug_info(f'[$] File is identified as Vaccination Record Processing vaccination many to one {filename}')
            records = process_record(client, file_content, 'vaccination', filename)
            return {"filename": filename, "records": records, "type": 'vaccination'}
        elif classification == 'Certification':
            log_debug_info(f'[$] File is identified as Certification, processing certification many to one {filename}')
            records = process_record(client, file_content, 'certification', filename)
            return {"filename": filename, "records": records, "type": 'certification'}
        else:
            log_debug_info(f'[F] Failed to classify the document correctly:{filename} : {classification}')
            return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process__file, list_of_file_names))

    for result in results:
        if result is not None:
            if result['type'] == 'vaccination':
                vaccine_consolidated_records.append({"filename": result['filename'], "records": result['records']})
            elif result['type'] == 'certification':
                certification_consolidated_records.append({"filename": result['filename'], "records": result['records']})

    log_debug_info(f'[D] Processing many to one complete, creating final file')

    # Extract name for the filenames
    if vaccine_consolidated_records:
        name = vaccine_consolidated_records[0]['records']['name']
            # Define the output filenames
        vaccine_output_filename = f"{name}_vaccination_records.json"

        # Dump the results to files
        json_vaccine_bytes = json.dumps(vaccine_consolidated_records).encode('utf-8')

        tdate = str(datetime.utcnow().isoformat()) + 'Z'

        metadata = {
            'name': vaccine_output_filename,
            'date': tdate,
            'status': 'processed',
            'label': 'vaccination_records',
            'cost': 'N/A',
            'process_time': 'N/A'
        }

        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=f"{user_id}/{vaccine_output_filename}", Body=json_vaccine_bytes, Metadata=metadata)

        return vaccine_output_filename
    elif certification_consolidated_records:
        name = certification_consolidated_records[0]['records']['name']
        # Define the output filenames
        certification_output_filename = f"{name}_certification.json"

        # Dump the results to files
        json_certification_bytes = json.dumps(certification_consolidated_records).encode('utf-8')

        tdate = str(datetime.utcnow().isoformat()) + 'Z'

        metadata = {
            'name': certification_output_filename,
            'date': tdate,
            'status': 'processed',
            'label': 'certification_records',
            'cost': 'N/A',
            'process_time': 'N/A'
        }

        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=f"{user_id}/{certification_output_filename}", Body=json_certification_bytes, Metadata=metadata)

        return certification_output_filename

    # Dump the results to a file
    # dump_data_to_file(results, "consolidated_records.json")
    
    # Load results from the file (optional for debugging)
    
    #loaded_results = load_data_from_file("consolidated_records.json")

    #vaccine_consolidated_records = loaded_results["vaccine_consolidated_records"]
    #certification_consolidated_records = loaded_results["certification_consolidated_records"]

    # final_html = create_final_html(vaccine_consolidated_records, certification_consolidated_records)

    # new_parser = HtmlToDocx()
    # doc = new_parser.parse_html_string(final_html)
    # output_stream = BytesIO()
    # doc.save(output_stream)

    log_debug_info("Error vaccine_consolidated_records and certification_consolidated_records empty")

    return f"Error vaccine_consolidated_records and certification_consolidated_records empty"

def process_record(client, file_content, record_type, filename):
    # Existing code for processing vaccination records
    doc = fitz.open(stream=file_content, filetype="pdf")
    records = []

    for page_num, page in enumerate(doc):
        # Render page to an image
        pix = page.get_pixmap(dpi=300)

        # Convert pixmap to a BytesIO object
        image_bytes = BytesIO(pix.tobytes("png"))

        image_bytes.seek(0)

        # Write the image bytes to a file
        #with open(f'{filename}_{page_num + 1}.png', "wb") as image_file:
        #    image_file.write(image_bytes.getbuffer())
        #image_bytes.seek(0)

        log_debug_info(f"[$] Processed image in memory for page {page_num+1}!")

        # Extract information from the image
        if record_type == 'vaccination':
            record = extract_vaccination_info(client, image_bytes, filename)
        elif record_type == 'certification':
            record = extract_certification_info(client, image_bytes, filename)
        records.append(record)
    if record_type == 'vaccination':
        consolidated_record = merge_records(records)
        return consolidated_record
    elif record_type == 'certification':
        return records

def merge_records(records):
    """
    Merge multiple vaccination records into a consolidated record.
    Args:
    records (list): List of individual records from different pages.
    
    Returns:
    dict: Merged vaccination record.
    """
    consolidated = {
        "name": "Not Specified",
        "religious_exemption": "Not Specified",
        "immunizations": []
    }
    
    for record in records:
        if record.name != "Not Specified":
            consolidated["name"] = record.name
        if record.religious_exemption != "Not Specified":
            consolidated["religious_exemption"] = record.religious_exemption
        consolidated["immunizations"].extend(record.immunizations)
    
    return consolidated

def create_final_html(vac_records, cert_records):
    # Determine the consolidated name from the records
    consolidated_name = "Not Specified"
    for item in vac_records + cert_records:
        if 'records' in item and isinstance(item['records'], list) and len(item['records']) > 0:
            if hasattr(item['records'][0], 'name') and item['records'][0].name != "Not Specified":
                consolidated_name = item['records'][0].name
                break

    final_html = "<html><body>"

    # Title
    final_html += f"<h1>{consolidated_name}</h1>"

    # Process vaccination records
    final_html += "<h1>Immunization Records</h1>"
    for item in vac_records:
        filename = item['filename']
        record = item['records']
        immunizations_html = "".join([
            f"<li>{immunization.type} on {immunization.date}</li>" for immunization in record['immunizations']
        ])
        final_html += f"""
        <h2>{filename}</h2>
        <p>Religious Exemption: {record['religious_exemption']}</p>
        <ul>{immunizations_html}</ul>
        <hr/>
        """

    # Process certification records
    final_html += "<h1>Certifications</h1>"
    for item in cert_records:
        filename = item['filename']
        record = item['records']
        certifications_html = "".join([
            f"<li>{certification.type} issued on {certification.issue_date}, expires on {certification.expiration_date}</li>"
            for certification in record[0].certifications
        ])
        final_html += f"""
        <h2>{filename}</h2>
        <ul>{certifications_html}</ul>
        <hr/>
        """

    final_html += "</body></html>"
    return final_html