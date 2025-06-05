from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import MessageTemplate, MessageType
import uuid

router = APIRouter(prefix="/templates", tags=["Message Templates"])

class TemplateCreate(BaseModel):
    name: str = Field(..., example="Follow Up Email")
    message_type: MessageType = Field(..., example="email")
    subject: str = Field(None, example="Let's Connect")
    content: str = Field(..., example="Hi {{first_name}}, ...")

@router.post("/", response_model=dict)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    try:
        new_template = MessageTemplate(
            id=uuid.uuid4(),
            name=template.name,
            message_type=template.message_type,
            subject=template.subject,
            content=template.content,
            is_active=True
        )
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        return {
            "id": str(new_template.id),
            "name": new_template.name,
            "message_type": new_template.message_type,
            "subject": new_template.subject,
            "content": new_template.content,
            "is_active": new_template.is_active
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 