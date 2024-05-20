from spire.doc import *
from spire.doc.common import *
from pydantic import BaseModel, field_validator
import datetime
import os
import pdb

class License(BaseModel):
    license_name: str
    expiration: str

    @field_validator('license_name', 'expiration')
    def ensure_string(cls, v):
        return str(v) if v is not None else "Not Specified"


class Certification(BaseModel):
    certification_name: str
    expiration: str

    @field_validator('certification_name', 'expiration')
    def ensure_string(cls, v):
        return str(v) if v is not None else "Not Specified"

class PersonalDetails(BaseModel):
    name: str
    email: str
    phone: str
    secondary_phone: str
    fax: str
    address: str

    @field_validator('name', 'email', 'phone', 'secondary_phone', 'fax', 'address')
    def ensure_string(cls, v):
        return str(v) if v is not None else "Not Specified"

class EducationDetail(BaseModel):
    institution: str
    location: str
    degree: str
    major: str
    graduation_year: str
    contact: str
    
    @field_validator('institution','location','degree','major','graduation_year','contact')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'


class WorkExperience(BaseModel):
    position: str
    company: str
    department: str
    location: str
    start_date: str
    end_date: str
    description: str

    @field_validator('position','company','department','location','start_date','end_date','description')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'


class WorkExperienceList(BaseModel):
    experiences: List[WorkExperience]

class EducationList(BaseModel):
    educations: List[EducationDetail]

class CertificationList(BaseModel):
    certifications: List[Certification]

class LicenseList(BaseModel):
    licenses: List[License]

class SectionMetadata(BaseModel):
    header: str
    description: str
    entry_count: int


class Personal_Educational(BaseModel):
    pdetail: PersonalDetails
    edetail: EducationList

class License_Certification(BaseModel):
    licenses: LicenseList
    certifications: CertificationList



class SectionInfo(BaseModel):
    Type: str
    format: str
    number_of_items: str

    class Config:
        json_schema_extra = {
            "properties": {
                "Type": {
                    "description": "Indicates the type of the section (Personal Detail, Educational Details, Work Experience, Licenses, Certifications)"
                },
                "format": {
                    "description" : "Comment on the format or structure of this field"
                },
                "number_of_items": {
                    "description" : "Count how many items are in this section"
                }
            }
        }
    @field_validator('number_of_items')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'


class ResumeMetadata(BaseModel):
    personal_details: SectionInfo
    educational_details: SectionInfo
    work_experience: SectionInfo
    certifications: SectionInfo
    licenses: SectionInfo
    additional_comments: str

class ImmunizationRecord_Many_to_One(BaseModel):
    type: str
    date: str

    @field_validator('type', 'date')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'

class ImmunizationRecord_Many_to_One_List(BaseModel):
    name: str
    religious_exemption: str
    immunizations: List[ImmunizationRecord_Many_to_One]

    @field_validator('name', 'religious_exemption')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'


class Certification_Many_to_One(BaseModel):
    type: str
    issue_date: str
    expiration_date: str

    @field_validator('type', 'issue_date', 'expiration_date')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'


class Certification_Many_to_One_List(BaseModel):
    name: str
    certifications: List[Certification_Many_to_One]
    @field_validator('name')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'

class Classify_many_to_one(BaseModel):
    class_type: str
    @field_validator('class_type')
    def ensure_string(cls, v):
        if v is not None:
            return str(v)
        return 'Not Specified'



def log_debug_info(message):
    # Get the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create the log directory if it doesn't exist
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)
    
    # Create the log file path
    log_file = os.path.join(log_directory, "debug.log")
    
    # Write the log message with timestamp to the file
    with open(log_file, "a") as file:
        log_message = f"{timestamp} - {message}\n"
        file.write(log_message)