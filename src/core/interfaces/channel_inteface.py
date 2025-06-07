# src/core/interfaces/channel_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ChannelInterface(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the channel API"""
        pass
    
    @abstractmethod
    async def send_message(self, recipient_id: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to a recipient"""
        pass
    
    @abstractmethod
    async def get_profile(self, profile_id: str) -> Dict[str, Any]:
        """Retrieve profile information"""
        pass

    @abstractmethod
    async def track_engagement(self, message_id: str) -> Dict[str, Any]:
        """Track engagement metrics for a message"""
        pass