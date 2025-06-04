from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Content
from api.schemas.content import ContentCreate, ContentResponse
from uuid import uuid4
from datetime import datetime, timezone

router = APIRouter(prefix="/content", tags=["content"])

@router.post("/", response_model=ContentResponse)
def create_content(content: ContentCreate, db: Session = Depends(get_db)):
    """Create new content (e.g., landing page for CMS)."""
    # Check for duplicate name and type
    existing = db.query(Content).filter(
        Content.name == content.name,
        Content.content_type == content.content_type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Content with this name and type already exists")
    
    db_content = Content(
        id=uuid4(),
        name=content.name,
        content_type=content.content_type,
        data=content.data,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

@router.get("/{content_id}", response_model=ContentResponse)
def get_content(content_id: str, db: Session = Depends(get_db)):
    """Retrieve content by ID."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content