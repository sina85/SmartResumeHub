from utils import *
from spire.doc import *
from spire.doc.common import *
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

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

class ResumeMetadata(BaseModel):
    sections: List[SectionMetadata]
    keyword_density: dict  # Maps sections to keyword density information
    date_range: str
    formatting: str
    summary_content: str