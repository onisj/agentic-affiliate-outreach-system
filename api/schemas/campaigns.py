from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any
from uuid import UUID
from enum import Enum
from datetime import datetime

class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    template_id: str = Field(..., description="UUID of the message template")
    target_criteria: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('template_id')
    @classmethod
    def validate_template_id(cls, v):
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError('template_id must be a valid UUID')

class CampaignResponse(BaseModel):
    id: str
    name: str
    template_id: Optional[str] = None
    target_criteria: Dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('id', mode='before')
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v else None

    @field_validator('template_id', mode='before')
    @classmethod
    def serialize_template_id(cls, v):
        return str(v) if v else None

    @field_validator('status', mode='before')
    @classmethod
    def serialize_status(cls, v):
        return v.value if hasattr(v, 'value') else str(v)
