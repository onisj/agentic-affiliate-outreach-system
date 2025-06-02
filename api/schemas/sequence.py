from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class SequenceCreate(BaseModel):
    campaign_id: UUID
    step_number: int
    template_id: UUID
    delay_days: int
    condition: Optional[Dict[str, Any]] = {}

class SequenceResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    step_number: int
    template_id: UUID
    delay_days: int
    condition: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True