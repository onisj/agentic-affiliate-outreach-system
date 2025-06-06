from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Optional, Any
from uuid import UUID
from enum import Enum
from datetime import datetime

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

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

class CampaignBase(BaseModel):
    name: str
    description: str | None = None
    template_id: str | None = None
    target_criteria: dict | None = None
    status: str = "draft"
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Summer Outreach 2024",
                "description": "Outreach campaign for summer affiliates",
                "template_id": "template_123",
                "target_criteria": {
                    "min_score": 0.7,
                    "max_prospects": 100
                }
            }
        }
    )
