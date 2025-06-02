from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ContentCreate(BaseModel):
    name: str
    content_type: str  # e.g., "landing_page", "discovery_keywords"
    data: Dict[str, Any]

class ContentResponse(BaseModel):
    id: str
    name: str
    content_type: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True