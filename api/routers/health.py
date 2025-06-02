from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
def health_check():
    """Check the health of the system."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}