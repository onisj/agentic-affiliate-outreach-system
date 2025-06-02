from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import MessageLog, MessageStatus
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/sendgrid")
def handle_sendgrid_webhook(events: List[Dict[str, Any]], db: Session = Depends(get_db)):
    for event in events:
        message_id = event.get("sg_message_id")
        event_type = event.get("event")
        
        message_log = db.query(MessageLog).filter(MessageLog.id == message_id).first()
        if not message_log:
            continue
        
        if event_type == "open":
            message_log.status = MessageStatus.OPENED
            message_log.opened_at = datetime.utcnow()
        elif event_type == "click":
            message_log.status = MessageStatus.CLICKED
            message_log.clicked_at = datetime.utcnow()
        
        db.commit()
    
    return {"status": "processed"}