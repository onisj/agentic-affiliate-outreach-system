from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CampaignStatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class CampaignCreate(BaseModel):
    name: str
    template_id: str
    target_criteria: Optional[Dict[str, Any]] = None

class CampaignResponse(BaseModel):
    id: str
    name: str
    template_id: str
    target_criteria: Optional[Dict[str, Any]]
    status: CampaignStatusEnum
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True