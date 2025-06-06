from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class ContentCreate(BaseModel):
    """Schema for creating content (e.g., landing page)."""
    name: str
    content_type: str  # e.g., "landing_page", "survey_keywords"
    data: Dict[str, Any]  # Flexible JSON for content fields (e.g., title, headline)

class ContentResponse(BaseModel):
    """Schema for content response, including database metadata."""
    id: UUID
    name: str
    content_type: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)