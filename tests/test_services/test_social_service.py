# test_social_service.py
from services.social_service import SocialService
from database.session import SessionLocal
from sqlalchemy.orm import Session
import uuid

def test_twitter_dm():
    db: Session = SessionLocal()
    try:
        social_service = SocialService()
        result = social_service.send_twitter_dm(
            prospect_id=str(uuid.uuid4()),
            user_id="12345",  # Replace with a valid Twitter user ID
            template="Hi {{first_name}}, welcome to {{company}}!",
            prospect_data={"first_name": "John", "company": "Acme Corp"},
            campaign_id=str(uuid.uuid4()),
            db=db
        )
        print(result)
    finally:
        db.close()

if __name__ == "__main__":
    test_twitter_dm()