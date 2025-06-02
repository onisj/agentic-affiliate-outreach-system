from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProspectStatusEnum(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    DECLINED = "declined"
    ENROLLED = "enrolled"

class ProspectCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    social_profiles: Optional[Dict[str, Any]] = None
    lead_source: Optional[str] = None
    consent_given: bool = False

class ProspectUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    social_profiles: Optional[Dict[str, Any]] = None
    lead_source: Optional[str] = None
    consent_given: Optional[bool] = None
    status: Optional[ProspectStatusEnum] = None

class ProspectResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    website: Optional[str]
    social_profiles: Optional[Dict[str, Any]]
    lead_source: Optional[str]
    qualification_score: int
    consent_given: bool
    consent_timestamp: Optional[datetime]
    status: ProspectStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True