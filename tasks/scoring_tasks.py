from tasks.celery_app import celery_app
from sqlalchemy.orm import Session
from database.models import AffiliateProspect
from database.session import get_db
from services.scoring_service import LeadScoringService

@celery_app.task
def score_prospect(prospect_id: str):
    """Calculate and update prospect score."""
    db = next(get_db())
    scoring_service = LeadScoringService()
    
    try:
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
        if not prospect:
            return {"success": False, "error": "Prospect not found"}
        
        prospect_data = {
            'email': prospect.email,
            'first_name': prospect.first_name,
            'last_name': prospect.last_name,
            'company': prospect.company,
            'website': prospect.website,
            'social_profiles': prospect.social_profiles or {}
        }
        
        score = scoring_service.calculate_score(prospect_data)
        prospect.qualification_score = score
        if score >= 70:
            prospect.status = "qualified"
        
        db.commit()
        return {"success": True, "score": score}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()