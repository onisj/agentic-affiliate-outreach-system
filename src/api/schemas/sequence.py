from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime

class SequenceBase(BaseModel):
    """Base schema for sequence data"""
    step_number: int = Field(..., ge=1, description="Order of the sequence step")
    template_id: UUID = Field(..., description="ID of the message template to use")
    delay_days: int = Field(default=0, ge=0, description="Days to wait before executing this step")
    condition: Optional[Dict] = Field(default=None, description="Conditions for executing this step")

class SequenceCreate(SequenceBase):
    """Schema for creating a new sequence step"""
    campaign_id: UUID = Field(..., description="ID of the campaign this sequence belongs to")

class SequenceUpdate(BaseModel):
    """Schema for updating a sequence step"""
    step_number: Optional[int] = Field(None, ge=1, description="Order of the sequence step")
    template_id: Optional[UUID] = Field(None, description="ID of the message template to use")
    delay_days: Optional[int] = Field(None, ge=0, description="Days to wait before executing this step")
    condition: Optional[Dict] = Field(None, description="Conditions for executing this step")

    @field_validator('step_number')
    def validate_step_number(cls, v):
        if v is not None and v < 1:
            raise ValueError('step_number must be greater than 0')
        return v

    @field_validator('delay_days')
    def validate_delay_days(cls, v):
        if v is not None and v < 0:
            raise ValueError('delay_days must be non-negative')
        return v

class SequenceResponse(SequenceBase):
    """Schema for sequence response"""
    id: UUID
    campaign_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
