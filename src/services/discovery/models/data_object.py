"""
Data Object Model

This module defines the DataObject class for standardized data passing between components.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class PlatformType(str, Enum):
    """Enum for supported platform types."""
    LINKEDIN = "LinkedIn"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    TIKTOK = "TikTok"
    INSTAGRAM = "Instagram"
    REDDIT = "Reddit"
    GENERIC = "Generic"

class DataObject(BaseModel):
    """Standardized data object for passing data between components."""
    
    # Required fields
    platform: PlatformType = Field(..., description="The platform the data was scraped from")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the data was collected")
    url: str = Field(..., description="The URL that was scraped")
    
    # Optional fields
    data: Dict[str, Any] = Field(default_factory=dict, description="The scraped data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the scraping process")
    error: Optional[str] = Field(default=None, description="Error message if scraping failed")
    
    # Validation
    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the DataObject to a dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataObject':
        """Create a DataObject from a dictionary."""
        return cls(**data)
    
    def is_valid(self) -> bool:
        """Check if the DataObject is valid."""
        return self.error is None and bool(self.data)
    
    def get_platform(self) -> PlatformType:
        """Get the platform type."""
        return self.platform
    
    def get_timestamp(self) -> datetime:
        """Get the timestamp."""
        return self.timestamp
    
    def get_url(self) -> str:
        """Get the URL."""
        return self.url
    
    def get_data(self) -> Dict[str, Any]:
        """Get the scraped data."""
        return self.data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the metadata."""
        return self.metadata
    
    def get_error(self) -> Optional[str]:
        """Get the error message if any."""
        return self.error
    
    def set_error(self, error: str) -> None:
        """Set an error message."""
        self.error = error
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add a metadata key-value pair."""
        self.metadata[key] = value
    
    def update_data(self, key: str, value: Any) -> None:
        """Update a data key-value pair."""
        self.data[key] = value
    
    def merge_data(self, other_data: Dict[str, Any]) -> None:
        """Merge another data dictionary into this one."""
        self.data.update(other_data)
    
    def merge_metadata(self, other_metadata: Dict[str, Any]) -> None:
        """Merge another metadata dictionary into this one."""
        self.metadata.update(other_metadata)
    
    def __str__(self) -> str:
        """String representation of the DataObject."""
        return f"DataObject(platform={self.platform}, url={self.url}, timestamp={self.timestamp})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the DataObject."""
        return (
            f"DataObject(\n"
            f"  platform={self.platform},\n"
            f"  url={self.url},\n"
            f"  timestamp={self.timestamp},\n"
            f"  data={self.data},\n"
            f"  metadata={self.metadata},\n"
            f"  error={self.error}\n"
            f")"
        ) 