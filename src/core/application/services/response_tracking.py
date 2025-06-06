from sqlalchemy.orm import Session
from database.models import MessageLog, MessageStatus
from datetime import datetime
import pytz

class ResponseTrackingService:
    def __init__(self, db: Session):
        self.db = db

    def track_response(self, message_id: str, response_type: str, content: str) -> bool:
        """
        Track a response to a message.
        
        Args:
            message_id: The ID of the message being responded to
            response_type: The type of response (e.g., 'email', 'linkedin', 'twitter')
            content: The content of the response
            
        Returns:
            bool: True if tracking was successful, False otherwise
        """
        try:
            message = self.db.query(MessageLog).filter(MessageLog.id == message_id).first()
            if not message:
                return False
                
            message.status = MessageStatus.RESPONDED
            message.response_type = response_type
            message.response_content = content
            message.response_timestamp = datetime.now(pytz.UTC)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e

    def get_message_responses(self, prospect_id: str) -> list:
        """
        Get all responses for a prospect's messages.
        
        Args:
            prospect_id: The ID of the prospect
            
        Returns:
            list: List of message responses
        """
        try:
            messages = self.db.query(MessageLog).filter(
                MessageLog.prospect_id == prospect_id,
                MessageLog.status == MessageStatus.RESPONDED
            ).all()
            
            return [
                {
                    'message_id': msg.id,
                    'type': msg.message_type,
                    'content': msg.response_content,
                    'timestamp': msg.response_timestamp
                }
                for msg in messages
            ]
            
        except Exception as e:
            raise e