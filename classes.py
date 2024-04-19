from utils import *
from spire.doc import *
from spire.doc.common import *
from pydantic import BaseModel, field_validator

class License(BaseModel):
    license_type: str
    license_number: str
    state_or_country: str
    expiration: str

    @field_validator('license_type', 'license_number', 'state_or_country', 'expiration')
    def ensure_string(cls, v):
        return str(v) if v is not None else "Not Specified"


class Certification(BaseModel):
    certification_name: str
    issuing_organization: str
    expiration: str

    @field_validator('certification_name', 'issuing_organization', 'expiration')
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
    honors: str
    contact: str
    
    @field_validator('institution','location','degree','major','graduation_year','honors','contact')
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
    hours_worked: str
    description: str

    @field_validator('position','company','department','location','start_date','end_date','hours_worked','description')
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