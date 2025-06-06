from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

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
    id: UUID
    name: str
    subject: Optional[str]
    content: str
    message_type: MessageTypeEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)