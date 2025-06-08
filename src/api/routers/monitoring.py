from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database.session import get_db
from services.monitoring import MonitoringService, AlertConfig
from database.models import Alert, AlertType, AlertSeverity, SystemMetric, WebhookMetric
from pydantic import BaseModel, HttpUrl, EmailStr, ConfigDict
from typing import Optional

router = APIRouter()

class AlertConfigCreate(BaseModel):
    webhook_url: Optional[HttpUrl] = None
    email_recipients: Optional[List[EmailStr]] = None
    slack_webhook_url: Optional[HttpUrl] = None
    failure_rate_threshold: float = 0.1
    consecutive_failures_threshold: int = 5
    notification_cooldown_minutes: int = 15
    model_config = ConfigDict(from_attributes=True)

class AlertUpdate(BaseModel):
    is_resolved: bool
    resolution_notes: Optional[str] = None

@router.post("/monitoring/config", response_model=Dict[str, Any])
def update_alert_config(
    config: AlertConfigCreate,
    db: Session = Depends(get_db)
):
    """Update alert configuration."""
    monitoring_service = MonitoringService(db)
    monitoring_service.update_alert_config(
        webhook_url=str(config.webhook_url) if config.webhook_url else None,
        email_recipients=config.email_recipients,
        slack_webhook_url=str(config.slack_webhook_url) if config.slack_webhook_url else None,
        failure_rate_threshold=config.failure_rate_threshold,
        consecutive_failures_threshold=config.consecutive_failures_threshold,
        notification_cooldown_minutes=config.notification_cooldown_minutes
    )
    return {"message": "Alert configuration updated successfully"}

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    alert_type: Optional[AlertType] = None,
    severity: Optional[AlertSeverity] = None,
    is_resolved: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering."""
    query = db.query(Alert)
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    if start_date:
        query = query.filter(Alert.created_at >= start_date)
    if end_date:
        query = query.filter(Alert.created_at <= end_date)
    
    return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()

@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update alert status and resolution notes."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = update.is_resolved
    if update.is_resolved:
        alert.resolved_at = datetime.utcnow()
    if update.resolution_notes:
        alert.resolution_notes = update.resolution_notes
    
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/metrics/system", response_model=List[SystemMetricResponse])
def get_system_metrics(
    metric_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get system metrics with optional filtering."""
    query = db.query(SystemMetric)
    
    if metric_name:
        query = query.filter(SystemMetric.metric_name == metric_name)
    if start_date:
        query = query.filter(SystemMetric.timestamp >= start_date)
    if end_date:
        query = query.filter(SystemMetric.timestamp <= end_date)
    
    return query.order_by(SystemMetric.timestamp.desc()).limit(limit).all()

@router.get("/metrics/webhook/{webhook_id}", response_model=List[WebhookMetricResponse])
def get_webhook_metrics(
    webhook_id: int,
    metric_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get webhook-specific metrics with optional filtering."""
    query = db.query(WebhookMetric).filter(WebhookMetric.webhook_id == webhook_id)
    
    if metric_name:
        query = query.filter(WebhookMetric.metric_name == metric_name)
    if start_date:
        query = query.filter(WebhookMetric.timestamp >= start_date)
    if end_date:
        query = query.filter(WebhookMetric.timestamp <= end_date)
    
    return query.order_by(WebhookMetric.timestamp.desc()).limit(limit).all()

@router.get("/metrics/summary", response_model=Dict[str, Any])
def get_metrics_summary(
    time_range: str = Query("1h", regex="^[0-9]+[mhd]$"),
    db: Session = Depends(get_db)
):
    """Get summary of system metrics for the specified time range."""
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_system_metrics(time_range)

@router.get("/metrics/webhook/{webhook_id}/summary", response_model=Dict[str, Any])
def get_webhook_metrics_summary(
    webhook_id: int,
    time_range: str = Query("1h", regex="^[0-9]+[mhd]$"),
    db: Session = Depends(get_db)
):
    """Get summary of webhook-specific metrics for the specified time range."""
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_webhook_metrics(webhook_id, time_range) 