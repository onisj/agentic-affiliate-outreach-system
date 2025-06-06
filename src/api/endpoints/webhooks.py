from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from database.models import WebhookEventType, Webhook, WebhookDelivery, MessageStatus, ProspectStatus, CampaignStatus
from app.services.webhook_service import (
    WebhookService, EVENT_SCHEMAS, LoadTestConfig, LoadTestResult,
    ConcurrentTestConfig, ConcurrentTestResult, StressTestConfig,
    StressTestResult, SpikeTestConfig, SpikeTestResult
)
from database.session import get_db
import json
from datetime import datetime, timezone, timedelta
import uuid
import time
import statistics

router = APIRouter()

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[WebhookEventType]
    description: Optional[str] = None

class WebhookResponse(BaseModel):
    id: str
    url: str
    events: List[WebhookEventType]
    is_active: bool
    description: Optional[str]
    failure_count: int
    last_triggered_at: Optional[str]

class WebhookDeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: WebhookEventType
    success: bool
    response_code: Optional[int]
    created_at: str
    error_message: Optional[str]

class WebhookStats(BaseModel):
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    avg_response_time: float
    retry_stats: Dict[str, int]

class WebhookTestPayload(BaseModel):
    event_type: WebhookEventType
    payload: Dict[str, Any] = Field(..., description="Test payload to send")
    validate: bool = Field(True, description="Whether to validate the payload against schema")

class WebhookTestResponse(BaseModel):
    success: bool
    validation_result: Optional[Dict[str, Any]]
    delivery_result: Optional[Dict[str, Any]]
    error: Optional[str]

class WebhookTestScenario(BaseModel):
    name: str
    description: str
    event_type: WebhookEventType
    payload: Dict[str, Any]
    expected_response: Optional[Dict[str, Any]]

class WebhookTestResult(BaseModel):
    scenario_name: str
    success: bool
    response_time: float
    status_code: Optional[int]
    error: Optional[str]
    response_body: Optional[str]

class WebhookTestSuite(BaseModel):
    name: str
    description: str
    scenarios: List[WebhookTestScenario]

@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    db: Session = Depends(get_db)
):
    """Create a new webhook configuration."""
    service = WebhookService(db)
    result = await service.create_webhook(
        url=str(webhook.url),
        events=webhook.events,
        description=webhook.description
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result["webhook"]

@router.get("/webhooks/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: str,
    event_type: Optional[WebhookEventType] = None,
    success: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get delivery history for a webhook."""
    service = WebhookService(db)
    deliveries = await service.get_webhook_deliveries(
        webhook_id=webhook_id,
        event_type=event_type,
        success=success,
        limit=limit
    )
    return deliveries

@router.post("/webhooks/{webhook_id}/verify")
async def verify_webhook_signature(
    webhook_id: str,
    request: Request,
    x_webhook_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """Verify a webhook signature."""
    if not x_webhook_signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature")
    
    # Get webhook secret
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Get request body
    body = await request.body()
    payload = body.decode()
    
    # Verify signature
    service = WebhookService(db)
    is_valid = await service.verify_webhook_signature(
        payload=payload,
        signature=x_webhook_signature,
        secret=webhook.secret
    )
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    return {"success": True, "message": "Signature verified"}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """Test a webhook configuration with a sample payload."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    result = await service._deliver_webhook(
        webhook=webhook,
        event_type=WebhookEventType.MESSAGE_OPENED,
        payload={
            "test": True,
            "message": "This is a test webhook delivery",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/webhooks/dashboard", response_model=Dict[str, Any])
async def get_webhook_dashboard(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get webhook dashboard data."""
    service = WebhookService(db)
    
    # Get overall stats
    overall_stats = await service.get_webhook_stats(
        start_date=start_date,
        end_date=end_date
    )
    
    # Get webhook list with basic info
    webhooks = db.query(Webhook).all()
    webhook_list = [{
        "id": str(w.id),
        "url": w.url,
        "events": w.events,
        "is_active": w.is_active,
        "failure_count": w.failure_count,
        "last_triggered_at": w.last_triggered_at.isoformat() if w.last_triggered_at else None
    } for w in webhooks]
    
    # Get recent failures
    recent_failures = db.query(WebhookDelivery).filter(
        WebhookDelivery.success == False,
        WebhookDelivery.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
    ).order_by(
        WebhookDelivery.created_at.desc()
    ).limit(10).all()
    
    failure_list = [{
        "id": str(f.id),
        "webhook_id": str(f.webhook_id),
        "event_type": f.event_type,
        "error_message": f.error_message,
        "created_at": f.created_at.isoformat(),
        "retry_count": f.retry_count
    } for f in recent_failures]
    
    return {
        "overall_stats": overall_stats,
        "webhooks": webhook_list,
        "recent_failures": failure_list
    }

@router.get("/webhooks/{webhook_id}/stats", response_model=WebhookStats)
async def get_webhook_stats(
    webhook_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific webhook."""
    service = WebhookService(db)
    stats = await service.get_webhook_stats(
        webhook_id=webhook_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not stats["success"]:
        raise HTTPException(status_code=400, detail=stats["error"])
    
    return stats

@router.post("/webhooks/{webhook_id}/retry-failed")
async def retry_failed_deliveries(
    webhook_id: str,
    max_age_hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    db: Session = Depends(get_db)
):
    """Retry failed webhook deliveries within the specified time window."""
    service = WebhookService(db)
    
    # Get failed deliveries
    failed_deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.success == False,
        WebhookDelivery.created_at >= datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    ).all()
    
    if not failed_deliveries:
        return {"success": True, "message": "No failed deliveries to retry"}
    
    # Retry each delivery
    results = []
    for delivery in failed_deliveries:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            continue
            
        result = await service._deliver_webhook_with_retry(
            webhook=webhook,
            event_type=delivery.event_type,
            payload=delivery.payload
        )
        results.append({
            "delivery_id": str(delivery.id),
            "success": result["success"]
        })
    
    return {
        "success": True,
        "retried_count": len(results),
        "results": results
    }

@router.post("/webhooks/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: str,
    active: bool,
    db: Session = Depends(get_db)
):
    """Enable or disable a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook.is_active = active
    db.commit()
    
    return {
        "success": True,
        "message": f"Webhook {'enabled' if active else 'disabled'} successfully"
    }

@router.post("/webhooks/{webhook_id}/test-payload", response_model=WebhookTestResponse)
async def test_webhook_payload(
    webhook_id: str,
    test_data: WebhookTestPayload,
    db: Session = Depends(get_db)
):
    """Test a webhook with a custom payload."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    
    # Validate payload if requested
    validation_result = None
    if test_data.validate:
        is_valid = service._validate_payload(test_data.event_type, test_data.payload)
        validation_result = {
            "is_valid": is_valid,
            "schema": EVENT_SCHEMAS.get(test_data.event_type).schema_json() if EVENT_SCHEMAS.get(test_data.event_type) else None
        }
        if not is_valid:
            return WebhookTestResponse(
                success=False,
                validation_result=validation_result,
                error="Payload validation failed"
            )
    
    # Send test webhook
    try:
        delivery_result = await service._deliver_webhook_with_retry(
            webhook=webhook,
            event_type=test_data.event_type,
            payload=test_data.payload
        )
        
        return WebhookTestResponse(
            success=True,
            validation_result=validation_result,
            delivery_result=delivery_result
        )
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            validation_result=validation_result,
            error=str(e)
        )

@router.get("/webhooks/schemas")
async def get_webhook_schemas():
    """Get all available webhook event schemas."""
    return {
        event_type: schema.schema_json()
        for event_type, schema in EVENT_SCHEMAS.items()
    }

@router.post("/webhooks/{webhook_id}/simulate-event")
async def simulate_webhook_event(
    webhook_id: str,
    event_type: WebhookEventType,
    db: Session = Depends(get_db)
):
    """Simulate a real event for testing webhook delivery."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Generate sample payload based on event type
    sample_payload = {
        "message_id": str(uuid.uuid4()),
        "prospect_id": str(uuid.uuid4()),
        "campaign_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "external_message_id": f"test_{int(time.time())}"
    }
    
    # Add event-specific fields
    if event_type == WebhookEventType.MESSAGE_OPENED:
        sample_payload["opened_at"] = datetime.now(timezone.utc).isoformat()
    elif event_type == WebhookEventType.MESSAGE_CLICKED:
        sample_payload["clicked_at"] = datetime.now(timezone.utc).isoformat()
        sample_payload["click_url"] = "https://example.com/test"
    elif event_type == WebhookEventType.MESSAGE_REPLIED:
        sample_payload["replied_at"] = datetime.now(timezone.utc).isoformat()
        sample_payload["reply_analysis"] = {
            "sentiment": 0.5,
            "is_positive": True,
            "is_negative": False,
            "contains_questions": True,
            "contains_contact": False
        }
    elif event_type == WebhookEventType.PROSPECT_STATUS_CHANGED:
        sample_payload = {
            "prospect_id": str(uuid.uuid4()),
            "old_status": "new",
            "new_status": "interested",
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "triggered_by": "test"
        }
    elif event_type == WebhookEventType.CAMPAIGN_STATUS_CHANGED:
        sample_payload = {
            "campaign_id": str(uuid.uuid4()),
            "old_status": "draft",
            "new_status": "active",
            "changed_at": datetime.now(timezone.utc).isoformat()
        }
    
    # Send test webhook
    service = WebhookService(db)
    result = await service._deliver_webhook_with_retry(
        webhook=webhook,
        event_type=event_type,
        payload=sample_payload
    )
    
    return {
        "success": result["success"],
        "payload": sample_payload,
        "delivery_result": result
    }

@router.get("/webhooks/{webhook_id}/queue-status")
async def get_webhook_queue_status(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """Get the current status of the webhook delivery queue."""
    service = WebhookService(db)
    queue_size = service._delivery_queue.qsize()
    
    # Get recent deliveries
    recent_deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.created_at >= datetime.now(timezone.utc) - timedelta(minutes=5)
    ).order_by(
        WebhookDelivery.created_at.desc()
    ).all()
    
    return {
        "queue_size": queue_size,
        "recent_deliveries": [{
            "id": str(d.id),
            "event_type": d.event_type,
            "success": d.success,
            "created_at": d.created_at.isoformat(),
            "retry_count": d.retry_count
        } for d in recent_deliveries]
    }

@router.post("/webhooks/{webhook_id}/test-suite")
async def run_test_suite(
    webhook_id: str,
    test_suite: WebhookTestSuite,
    db: Session = Depends(get_db)
):
    """Run a suite of test scenarios against a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    results = []
    
    for scenario in test_suite.scenarios:
        start_time = time.time()
        try:
            # Validate payload
            is_valid = service._validate_payload(scenario.event_type, scenario.payload)
            if not is_valid:
                results.append(WebhookTestResult(
                    scenario_name=scenario.name,
                    success=False,
                    response_time=time.time() - start_time,
                    error="Payload validation failed"
                ))
                continue
            
            # Send test webhook
            delivery_result = await service._deliver_webhook_with_retry(
                webhook=webhook,
                event_type=scenario.event_type,
                payload=scenario.payload
            )
            
            results.append(WebhookTestResult(
                scenario_name=scenario.name,
                success=delivery_result["success"],
                response_time=time.time() - start_time,
                status_code=delivery_result.get("status_code"),
                response_body=delivery_result.get("response_body"),
                error=delivery_result.get("error")
            ))
            
        except Exception as e:
            results.append(WebhookTestResult(
                scenario_name=scenario.name,
                success=False,
                response_time=time.time() - start_time,
                error=str(e)
            ))
    
    return {
        "test_suite": test_suite.name,
        "total_scenarios": len(test_suite.scenarios),
        "successful_scenarios": sum(1 for r in results if r.success),
        "results": results
    }

@router.get("/webhooks/{webhook_id}/test-dashboard")
async def get_test_dashboard(
    webhook_id: str,
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: Session = Depends(get_db)
):
    """Get a comprehensive test dashboard for a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Calculate time range
    now = datetime.now(timezone.utc)
    if time_range == "1h":
        start_time = now - timedelta(hours=1)
    elif time_range == "24h":
        start_time = now - timedelta(days=1)
    elif time_range == "7d":
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # Get delivery statistics
    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.created_at >= start_time
    ).all()
    
    # Calculate metrics
    total_deliveries = len(deliveries)
    successful_deliveries = sum(1 for d in deliveries if d.success)
    failed_deliveries = total_deliveries - successful_deliveries
    
    # Calculate response time statistics
    response_times = []
    for delivery in deliveries:
        if delivery.response_code:
            response_times.append(
                (delivery.updated_at - delivery.created_at).total_seconds()
            )
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Get event type distribution
    event_type_distribution = {}
    for delivery in deliveries:
        event_type = delivery.event_type
        event_type_distribution[event_type] = event_type_distribution.get(event_type, 0) + 1
    
    # Get error distribution
    error_distribution = {}
    for delivery in deliveries:
        if not delivery.success and delivery.error_message:
            error_type = delivery.error_message.split(":")[0]
            error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
    
    # Get recent test results
    recent_tests = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.created_at >= now - timedelta(hours=1)
    ).order_by(
        WebhookDelivery.created_at.desc()
    ).limit(10).all()
    
    return {
        "overview": {
            "total_deliveries": total_deliveries,
            "success_rate": (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
            "avg_response_time": avg_response_time,
            "failure_rate": (failed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        },
        "event_type_distribution": event_type_distribution,
        "error_distribution": error_distribution,
        "recent_tests": [{
            "id": str(t.id),
            "event_type": t.event_type,
            "success": t.success,
            "response_code": t.response_code,
            "created_at": t.created_at.isoformat(),
            "response_time": (t.updated_at - t.created_at).total_seconds() if t.updated_at else None
        } for t in recent_tests],
        "time_range": time_range
    }

@router.get("/webhooks/test-scenarios")
async def get_test_scenarios():
    """Get a list of predefined test scenarios for different event types."""
    service = WebhookService(None)  # We only need the payload generation
    
    scenarios = []
    for event_type in WebhookEventType:
        payload = await service.generate_test_payload(event_type)
        scenarios.append({
            "name": f"Test {event_type.value}",
            "description": f"Test scenario for {event_type.value} event",
            "event_type": event_type,
            "payload": payload
        })
    
    return scenarios

@router.post("/webhooks/{webhook_id}/bulk-test")
async def run_bulk_test(
    webhook_id: str,
    event_types: List[WebhookEventType] = Body(...),
    count: int = Body(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Run multiple test deliveries for specified event types."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    results = []
    
    for event_type in event_types:
        for _ in range(count):
            payload = await service.generate_test_payload(event_type)
            start_time = time.time()
            
            try:
                delivery_result = await service._deliver_webhook_with_retry(
                    webhook=webhook,
                    event_type=event_type,
                    payload=payload
                )
                
                results.append({
                    "event_type": event_type,
                    "success": delivery_result["success"],
                    "response_time": time.time() - start_time,
                    "status_code": delivery_result.get("status_code"),
                    "error": delivery_result.get("error")
                })
                
            except Exception as e:
                results.append({
                    "event_type": event_type,
                    "success": False,
                    "response_time": time.time() - start_time,
                    "error": str(e)
                })
    
    # Calculate statistics
    success_count = sum(1 for r in results if r["success"])
    avg_response_time = sum(r["response_time"] for r in results) / len(results)
    
    return {
        "total_tests": len(results),
        "success_rate": (success_count / len(results) * 100) if results else 0,
        "avg_response_time": avg_response_time,
        "results": results
    }

@router.post("/webhooks/{webhook_id}/load-test", response_model=LoadTestResult)
async def run_load_test(
    webhook_id: str,
    config: LoadTestConfig,
    db: Session = Depends(get_db)
):
    """Run a load test on a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    result = await service.run_load_test(webhook, config)
    
    return result

@router.post("/webhooks/{webhook_id}/concurrent-test", response_model=ConcurrentTestResult)
async def run_concurrent_test(
    webhook_id: str,
    config: ConcurrentTestConfig,
    db: Session = Depends(get_db)
):
    """Run a concurrent test on a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    result = await service.run_concurrent_test(webhook, config)
    
    return result

@router.get("/webhooks/{webhook_id}/test-history")
async def get_test_history(
    webhook_id: str,
    test_type: Optional[str] = Query(None, regex="^(load|concurrent)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get history of load and concurrent tests for a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Get test deliveries
    query = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.payload["test_type"].astext == test_type if test_type else True
    )
    
    if start_date:
        query = query.filter(WebhookDelivery.created_at >= start_date)
    if end_date:
        query = query.filter(WebhookDelivery.created_at <= end_date)
    
    deliveries = query.order_by(
        WebhookDelivery.created_at.desc()
    ).limit(limit).all()
    
    # Group deliveries by test run
    test_runs = {}
    for delivery in deliveries:
        test_id = delivery.payload.get("test_id")
        if not test_id:
            continue
            
        if test_id not in test_runs:
            test_runs[test_id] = {
                "test_id": test_id,
                "test_type": delivery.payload.get("test_type"),
                "start_time": delivery.created_at,
                "end_time": delivery.updated_at,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "response_times": [],
                "error_distribution": {},
                "event_type_distribution": {}
            }
        
        run = test_runs[test_id]
        run["total_requests"] += 1
        if delivery.success:
            run["successful_requests"] += 1
        else:
            run["failed_requests"] += 1
            error_type = delivery.error_message.split(":")[0] if delivery.error_message else "Unknown error"
            run["error_distribution"][error_type] = run["error_distribution"].get(error_type, 0) + 1
        
        if delivery.response_code:
            response_time = (delivery.updated_at - delivery.created_at).total_seconds()
            run["response_times"].append(response_time)
        
        run["event_type_distribution"][delivery.event_type] = run["event_type_distribution"].get(delivery.event_type, 0) + 1
    
    # Calculate statistics for each test run
    for run in test_runs.values():
        if run["response_times"]:
            run["avg_response_time"] = statistics.mean(run["response_times"])
            run["min_response_time"] = min(run["response_times"])
            run["max_response_time"] = max(run["response_times"])
            run["p95_response_time"] = statistics.quantiles(run["response_times"], n=20)[18]
            run["p99_response_time"] = statistics.quantiles(run["response_times"], n=100)[98]
        else:
            run["avg_response_time"] = run["min_response_time"] = run["max_response_time"] = run["p95_response_time"] = run["p99_response_time"] = 0
        
        run["success_rate"] = (run["successful_requests"] / run["total_requests"] * 100) if run["total_requests"] > 0 else 0
        run["duration"] = (run["end_time"] - run["start_time"]).total_seconds()
    
    return {
        "total_test_runs": len(test_runs),
        "test_runs": list(test_runs.values())
    }

@router.get("/webhooks/{webhook_id}/test-metrics")
async def get_test_metrics(
    webhook_id: str,
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: Session = Depends(get_db)
):
    """Get aggregated metrics for all test runs."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Calculate time range
    now = datetime.now(timezone.utc)
    if time_range == "1h":
        start_time = now - timedelta(hours=1)
    elif time_range == "24h":
        start_time = now - timedelta(days=1)
    elif time_range == "7d":
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # Get test deliveries
    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.created_at >= start_time,
        WebhookDelivery.payload["test_type"].astext.in_(["load", "concurrent"])
    ).all()
    
    # Calculate metrics
    metrics = {
        "total_test_runs": 0,
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "avg_response_time": 0,
        "min_response_time": float("inf"),
        "max_response_time": 0,
        "p95_response_time": 0,
        "p99_response_time": 0,
        "error_distribution": {},
        "event_type_distribution": {},
        "test_type_distribution": {},
        "response_time_distribution": [],
        "success_rate_trend": [],
        "response_time_trend": []
    }
    
    # Process deliveries
    for delivery in deliveries:
        test_type = delivery.payload.get("test_type")
        if not test_type:
            continue
        
        metrics["total_requests"] += 1
        if delivery.success:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1
            error_type = delivery.error_message.split(":")[0] if delivery.error_message else "Unknown error"
            metrics["error_distribution"][error_type] = metrics["error_distribution"].get(error_type, 0) + 1
        
        if delivery.response_code:
            response_time = (delivery.updated_at - delivery.created_at).total_seconds()
            metrics["response_time_distribution"].append(response_time)
            metrics["min_response_time"] = min(metrics["min_response_time"], response_time)
            metrics["max_response_time"] = max(metrics["max_response_time"], response_time)
        
        metrics["event_type_distribution"][delivery.event_type] = metrics["event_type_distribution"].get(delivery.event_type, 0) + 1
        metrics["test_type_distribution"][test_type] = metrics["test_type_distribution"].get(test_type, 0) + 1
    
    # Calculate statistics
    if metrics["response_time_distribution"]:
        metrics["avg_response_time"] = statistics.mean(metrics["response_time_distribution"])
        metrics["p95_response_time"] = statistics.quantiles(metrics["response_time_distribution"], n=20)[18]
        metrics["p99_response_time"] = statistics.quantiles(metrics["response_time_distribution"], n=100)[98]
    
    # Calculate trends
    hourly_stats = {}
    for delivery in deliveries:
        hour = delivery.created_at.replace(minute=0, second=0, microsecond=0)
        if hour not in hourly_stats:
            hourly_stats[hour] = {"total": 0, "successful": 0, "response_times": []}
        
        stats = hourly_stats[hour]
        stats["total"] += 1
        if delivery.success:
            stats["successful"] += 1
        if delivery.response_code:
            response_time = (delivery.updated_at - delivery.created_at).total_seconds()
            stats["response_times"].append(response_time)
    
    # Sort and format trends
    for hour in sorted(hourly_stats.keys()):
        stats = hourly_stats[hour]
        metrics["success_rate_trend"].append({
            "timestamp": hour.isoformat(),
            "success_rate": (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
        })
        metrics["response_time_trend"].append({
            "timestamp": hour.isoformat(),
            "avg_response_time": statistics.mean(stats["response_times"]) if stats["response_times"] else 0
        })
    
    return metrics

@router.post("/webhooks/{webhook_id}/stress-test", response_model=StressTestResult)
async def run_stress_test(
    webhook_id: str,
    config: StressTestConfig,
    db: Session = Depends(get_db)
):
    """Run a stress test on a webhook to find its breaking point."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    result = await service.run_stress_test(webhook, config)
    
    return result

@router.post("/webhooks/{webhook_id}/spike-test", response_model=SpikeTestResult)
async def run_spike_test(
    webhook_id: str,
    config: SpikeTestConfig,
    db: Session = Depends(get_db)
):
    """Run a spike test on a webhook to test its behavior under sudden load."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    service = WebhookService(db)
    result = await service.run_spike_test(webhook, config)
    
    return result

@router.get("/webhooks/{webhook_id}/test-comparison")
async def compare_test_results(
    webhook_id: str,
    test_types: List[str] = Query(..., regex="^(load|concurrent|stress|spike)$"),
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: Session = Depends(get_db)
):
    """Compare results from different types of tests."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Calculate time range
    now = datetime.now(timezone.utc)
    if time_range == "1h":
        start_time = now - timedelta(hours=1)
    elif time_range == "24h":
        start_time = now - timedelta(days=1)
    elif time_range == "7d":
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # Get test deliveries
    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id,
        WebhookDelivery.created_at >= start_time,
        WebhookDelivery.payload["test_type"].astext.in_(test_types)
    ).all()
    
    # Group deliveries by test type
    test_results = {}
    for test_type in test_types:
        test_deliveries = [d for d in deliveries if d.payload.get("test_type") == test_type]
        
        if not test_deliveries:
            continue
        
        # Calculate metrics
        total_requests = len(test_deliveries)
        successful_requests = sum(1 for d in test_deliveries if d.success)
        failed_requests = total_requests - successful_requests
        
        # Calculate response times
        response_times = []
        for delivery in test_deliveries:
            if delivery.response_code:
                response_times.append(
                    (delivery.updated_at - delivery.created_at).total_seconds()
                )
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            p99_response_time = statistics.quantiles(response_times, n=100)[98]
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        # Get error distribution
        error_distribution = {}
        for delivery in test_deliveries:
            if not delivery.success and delivery.error_message:
                error_type = delivery.error_message.split(":")[0]
                error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
        
        # Get event type distribution
        event_type_distribution = {}
        for delivery in test_deliveries:
            event_type = delivery.event_type
            event_type_distribution[event_type] = event_type_distribution.get(event_type, 0) + 1
        
        # Calculate success rate trend
        hourly_stats = {}
        for delivery in test_deliveries:
            hour = delivery.created_at.replace(minute=0, second=0, microsecond=0)
            if hour not in hourly_stats:
                hourly_stats[hour] = {"total": 0, "successful": 0}
            
            stats = hourly_stats[hour]
            stats["total"] += 1
            if delivery.success:
                stats["successful"] += 1
        
        success_rate_trend = [
            {
                "timestamp": hour.isoformat(),
                "success_rate": (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
            }
            for hour, stats in sorted(hourly_stats.items())
        ]
        
        test_results[test_type] = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
            "error_distribution": error_distribution,
            "event_type_distribution": event_type_distribution,
            "success_rate_trend": success_rate_trend
        }
    
    return {
        "time_range": time_range,
        "test_types": test_types,
        "results": test_results
    } 