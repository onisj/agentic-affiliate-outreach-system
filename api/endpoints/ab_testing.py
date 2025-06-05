from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.ab_testing import ABTestingService
from database.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ab-testing", tags=["A/B Testing"])

class TestCreate(BaseModel):
    campaign_id: int
    template_ids: List[int]
    test_duration_days: int = 7
    sample_size_per_variant: int = 100

class TestResults(BaseModel):
    test_config: Dict[str, Any]
    metric: str
    results: Dict[int, float]
    analysis: Dict[str, Any]

@router.post("/tests", response_model=Dict[str, Any])
def create_test(test: TestCreate, db: Session = Depends(get_db)):
    """Create a new A/B test."""
    try:
        service = ABTestingService()
        result = service.create_test(
            campaign_id=test.campaign_id,
            template_ids=test.template_ids,
            test_duration_days=test.test_duration_days,
            sample_size_per_variant=test.sample_size_per_variant
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{campaign_id}/results", response_model=TestResults)
def get_test_results(
    campaign_id: int,
    metric: Optional[str] = None,
    confidence_level: float = 0.95,
    db: Session = Depends(get_db)
):
    """Get A/B test results for a campaign."""
    try:
        service = ABTestingService()
        result = service.get_test_results(
            campaign_id=campaign_id,
            metric=metric,
            confidence_level=confidence_level
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{campaign_id}/export")
def export_test_results(campaign_id: int, db: Session = Depends(get_db)):
    """Export A/B test results to a report."""
    try:
        service = ABTestingService()
        output_path = service.export_test_results(campaign_id)
        if output_path:
            return {"message": "Results exported successfully", "path": output_path}
        else:
            raise HTTPException(status_code=500, detail="Failed to export results")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
def list_available_metrics():
    """List all available metrics for A/B testing."""
    service = ABTestingService()
    return {"metrics": list(service.metrics.keys())} 