from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class MessageTypeEnum(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"

class TemplateCreate(BaseModel):
    name: str
    subject: Optional[str] = None
    content: str
    message_type: str = "email"

class TemplateResponse(BaseModel):
    id: str
    name: str
    subject: Optional[str]
    content: str
    message_type: MessageTypeEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True