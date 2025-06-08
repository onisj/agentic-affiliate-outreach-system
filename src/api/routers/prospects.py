from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from services.prospect_scoring import ProspectScoringService
from database.models import User, AffiliateProspect
from database.session import get_db
from services.visualization_service import VisualizationService
import os
from pydantic import BaseModel
import json
from services.cache_service import cache_result, cache
from sqlalchemy import func, desc
from api.dependencies import get_current_user
import logging
from database.session import get_db
from database.models import Prospect, Campaign
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
scoring_service = ProspectScoringService()

class ProspectScore(BaseModel):
    prospect_id: int
    score: float
    features: dict

class ScoringMetrics(BaseModel):
    total_prospects: int
    scored_prospects: int
    score_distribution: dict
    model_metrics: dict

# Cache warming functions
async def warm_top_prospects():
    """Warm cache with top prospects data."""
    db = next(get_db())
    try:
        # Get top prospects based on qualification score
        prospects = db.query(AffiliateProspect)\
            .order_by(desc(AffiliateProspect.qualification_score))\
            .limit(100)\
            .all()
        return [prospect.to_dict() for prospect in prospects]
    except Exception as e:
        logger.error(f"Error warming top prospects cache: {e}")
        return None

async def warm_prospect_stats():
    """Warm cache with prospect statistics."""
    db = next(get_db())
    try:
        stats = {
            'total_prospects': db.query(func.count(AffiliateProspect.id)).scalar(),
            'qualified_prospects': db.query(func.count(AffiliateProspect.id))
                .filter(AffiliateProspect.qualification_score >= 0.7)
                .scalar(),
            'active_prospects': db.query(func.count(AffiliateProspect.id))
                .filter(AffiliateProspect.status == 'active')
                .scalar(),
            'prospects_by_source': dict(
                db.query(AffiliateProspect.lead_source, func.count(AffiliateProspect.id))
                .group_by(AffiliateProspect.lead_source)
                .all()
            )
        }
        return stats
    except Exception as e:
        logger.error(f"Error warming prospect stats cache: {e}")
        return None

# Start cache warming
cache.warmer.start_warming("prospects:top", warm_top_prospects, ttl=300, interval=240)  # 5 min TTL, 4 min interval
cache.warmer.start_warming("prospects:stats", warm_prospect_stats, ttl=300, interval=240)

@router.post("/{prospect_id}/score", response_model=Dict[str, Any])
@cache_result(ttl=3600, key_prefix="prospect_score")  # Cache for 1 hour
def score_prospect(
    prospect_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate and return the score for a specific prospect."""
    try:
        prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
        if not prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")
        
        scoring_service = ProspectScoringService()
        score_data = scoring_service.calculate_prospect_score(prospect, db)
        
        # Update the prospect's score
        prospect.qualification_score = score_data['overall_score']
        db.commit()
        
        return score_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/score", response_model=Dict[str, Any])
def score_prospects_batch(
    batch_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Score a batch of prospects."""
    try:
        scoring_service = ProspectScoringService()
        result = scoring_service.update_prospect_scores(db, batch_size)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visualize", response_model=Dict[str, str])
def generate_visualizations(
    batch_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate visualizations for prospect scores."""
    try:
        # Get prospect scores
        scoring_service = ProspectScoringService()
        result = scoring_service.update_prospect_scores(db, batch_size)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        # Generate visualizations
        visualization_service = VisualizationService()
        visualization_paths = visualization_service.generate_all_visualizations(result['results'])
        
        # Convert paths to URLs
        base_url = "/static/visualizations"
        visualization_urls = {
            viz_type: f"{base_url}/{os.path.basename(path)}"
            for viz_type, path in visualization_paths.items()
        }
        
        return visualization_urls
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prospects/{prospect_id}/score", response_model=ProspectScore)
async def score_prospect(
    prospect_id: int,
    db: Session = Depends(get_db)
):
    """Score a specific prospect."""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    score = scoring_service.score_prospect(prospect)
    features = scoring_service._extract_features(prospect)
    
    return {
        "prospect_id": prospect_id,
        "score": score,
        "features": features
    }

@router.get("/campaigns/{campaign_id}/top-prospects", response_model=List[ProspectScore])
@cache_result(ttl=1800, key_prefix="top_prospects")  # Cache for 30 minutes
async def get_top_prospects(
    campaign_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top prospects for a campaign based on scores."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    top_prospects = scoring_service.get_top_prospects(campaign_id, limit)
    
    return [
        {
            "prospect_id": prospect.id,
            "score": prospect.score,
            "features": scoring_service._extract_features(prospect)
        }
        for prospect in top_prospects
    ]

@router.post("/prospects/score-batch", response_model=List[ProspectScore])
async def score_prospects_batch(
    prospect_ids: List[int],
    db: Session = Depends(get_db)
):
    """Score multiple prospects in batch."""
    prospects = db.query(Prospect).filter(Prospect.id.in_(prospect_ids)).all()
    if not prospects:
        raise HTTPException(status_code=404, detail="No prospects found")
    
    results = []
    for prospect in prospects:
        score = scoring_service.score_prospect(prospect)
        features = scoring_service._extract_features(prospect)
        results.append({
            "prospect_id": prospect.id,
            "score": score,
            "features": features
        })
    
    return results

@router.post("/model/train")
async def train_model(
    db: Session = Depends(get_db)
):
    """Train the prospect scoring model."""
    try:
        scoring_service.train_model()
        return {"message": "Model trained successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/metrics", response_model=ScoringMetrics)
async def get_scoring_metrics(
    db: Session = Depends(get_db)
):
    """Get current scoring metrics and model performance."""
    try:
        metrics_path = scoring_service.export_scoring_metrics()
        if not metrics_path:
            raise HTTPException(status_code=500, detail="Failed to export metrics")
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prospects/{prospect_id}/features", response_model=dict)
async def get_prospect_features(
    prospect_id: int,
    db: Session = Depends(get_db)
):
    """Get the features used for scoring a prospect."""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    features = scoring_service._extract_features(prospect)
    return features

@router.get("/prospects/", response_model=List[dict])
@cache_result(ttl=300, key_prefix="prospects")
async def list_prospects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List prospects with optional filters."""
    query = db.query(AffiliateProspect)
    
    if status:
        query = query.filter(AffiliateProspect.status == status)
    if min_score is not None:
        query = query.filter(AffiliateProspect.qualification_score >= min_score)
    
    prospects = query.offset(skip).limit(limit).all()
    return [prospect.to_dict() for prospect in prospects]

@router.get("/prospects/top", response_model=List[dict])
@cache_result(ttl=300, key_prefix="prospects")
async def get_top_prospects(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get top prospects by qualification score."""
    prospects = db.query(AffiliateProspect)\
        .order_by(desc(AffiliateProspect.qualification_score))\
        .limit(limit)\
        .all()
    return [prospect.to_dict() for prospect in prospects]

@router.get("/prospects/stats", response_model=dict)
@cache_result(ttl=300, key_prefix="prospects")
async def get_prospect_stats(db: Session = Depends(get_db)):
    """Get prospect statistics."""
    stats = {
        'total_prospects': db.query(func.count(AffiliateProspect.id)).scalar(),
        'qualified_prospects': db.query(func.count(AffiliateProspect.id))
            .filter(AffiliateProspect.qualification_score >= 0.7)
            .scalar(),
        'active_prospects': db.query(func.count(AffiliateProspect.id))
            .filter(AffiliateProspect.status == 'active')
            .scalar(),
        'prospects_by_source': dict(
            db.query(AffiliateProspect.lead_source, func.count(AffiliateProspect.id))
            .group_by(AffiliateProspect.lead_source)
            .all()
        )
    }
    return stats

@router.post("/prospects/", response_model=dict)
@cache.invalidate_on_update("prospects:*")
async def create_prospect(
    prospect: dict,
    db: Session = Depends(get_db)
):
    """Create a new prospect."""
    new_prospect = AffiliateProspect(**prospect)
    db.add(new_prospect)
    db.commit()
    db.refresh(new_prospect)
    return new_prospect.to_dict()

@router.put("/prospects/{prospect_id}", response_model=dict)
@cache.invalidate_on_update("prospects:*")
async def update_prospect(
    prospect_id: str,
    prospect: dict,
    db: Session = Depends(get_db)
):
    """Update an existing prospect."""
    existing_prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
    if not existing_prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    for key, value in prospect.items():
        setattr(existing_prospect, key, value)
    
    db.commit()
    db.refresh(existing_prospect)
    return existing_prospect.to_dict()

@router.delete("/prospects/{prospect_id}")
@cache.invalidate_on_update("prospects:*")
async def delete_prospect(
    prospect_id: str,
    db: Session = Depends(get_db)
):
    """Delete a prospect."""
    prospect = db.query(AffiliateProspect).filter(AffiliateProspect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    db.delete(prospect)
    db.commit()
    return {"message": "Prospect deleted successfully"} 