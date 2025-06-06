import pytest
from datetime import datetime, timedelta, timezone
from app.services.monitoring import MonitoringService, AlertType, AlertSeverity, AlertConfig
from app.services.logging_service import LoggingService
from database.models import Alert, SystemMetric, WebhookMetric
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock
from prometheus_client import REGISTRY
import traceback

@pytest.fixture(autouse=True)
def reset_prometheus_registry():
    """Reset the Prometheus registry before each test."""
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    yield

@pytest.fixture
def logger():
    """Create a logger instance for testing."""
    return LoggingService(enable_console=False)

@pytest.fixture
def db_session():
    """Create a mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def monitoring_service(logger, db_session):
    """Create a monitoring service instance for testing."""
    alert_config = AlertConfig(
        webhook_url="http://test-webhook.com",
        slack_webhook_url="http://test-slack.com",
        email_recipients=["test@example.com"],
        alert_thresholds={"failure_rate": 0.5},
        notification_cooldown=300
    )
    with patch('services.monitoring_service.start_http_server'):
        return MonitoringService(
            logger=logger,
            db=db_session,
            alert_config=alert_config
        )

@pytest.mark.asyncio
async def test_create_alert(monitoring_service, db_session):
    """Test alert creation."""
    def commit_side_effect(*args, **kwargs):
        print(f'\ndb.commit called! id(self)={id(db_session)} Stack trace:')
        traceback.print_stack()
        if commit_side_effect.called:
            print('\ndb.commit called more than once! Stack trace:')
            traceback.print_stack()
        commit_side_effect.called = True
    commit_side_effect.called = False
    db_session.commit.side_effect = commit_side_effect
    labels_mock = Mock()
    labels_mock.inc = Mock()
    labels_mock.dec = Mock()
    with patch('services.monitoring_service.ACTIVE_ALERTS.labels', return_value=labels_mock):
        with patch.object(monitoring_service, '_send_notifications', return_value=None):
            alert = await monitoring_service._create_alert(
                alert_type=AlertType.HIGH_FAILURE_RATE,
                severity=AlertSeverity.CRITICAL,
                message="Test alert",
                alert_metadata={"metric": "failure_rate", "value": 0.5},
                skip_notifications=True
            )
    assert isinstance(alert, Alert)
    assert alert.alert_type == AlertType.HIGH_FAILURE_RATE
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.message == "Test alert"
    assert alert.alert_metadata == {"metric": "failure_rate", "value": 0.5}
    assert alert.is_resolved is False
    db_session.add.assert_called_once_with(alert)
    db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_track_webhook_delivery(monitoring_service, db_session):
    """Test webhook delivery tracking."""
    webhook_id = 1
    event_type = "test_event"
    duration = 0.5
    success = True
    error = None
    
    # Mock the check_alert_conditions method
    with patch.object(monitoring_service, 'check_alert_conditions', new=AsyncMock()) as mock_check:
        await monitoring_service.track_webhook_delivery(
            webhook_id=webhook_id,
            event_type=event_type,
            duration=duration,
            success=success,
            error=error
        )
        
        # Verify the metric was created and added to the database
        db_session.add.assert_called_once()
        metric = db_session.add.call_args[0][0]
        assert isinstance(metric, WebhookMetric)
        assert metric.webhook_id == webhook_id
        assert metric.metric_name == "delivery_success"
        assert metric.metric_value == 1.0
        
        # Verify the alert check was called
        mock_check.assert_awaited_once_with(webhook_id)

@pytest.mark.asyncio
async def test_track_message_processing(monitoring_service):
    """Test message processing tracking."""
    message_type = "test_message"
    duration = 0.5
    success = True
    error = None
    
    with patch.object(monitoring_service, '_create_alert', new=AsyncMock()) as mock_create_alert:
        await monitoring_service.track_message_processing(
            message_type=message_type,
            duration=duration,
            success=success,
            error=error
        )
        mock_create_alert.assert_not_called()

@pytest.mark.asyncio
async def test_track_message_processing_error(monitoring_service):
    """Test message processing error tracking."""
    message_type = "test_message"
    duration = 0.5
    success = False
    error = "Test error"
    
    with patch.object(monitoring_service, '_create_alert', new=AsyncMock()) as mock_create_alert:
        await monitoring_service.track_message_processing(
            message_type=message_type,
            duration=duration,
            success=success,
            error=error
        )
        mock_create_alert.assert_awaited_once_with(
            alert_type=AlertType.MESSAGE_PROCESSING_ERROR,
            severity=AlertSeverity.ERROR,
            message=f"Message processing failed: {error}",
            alert_metadata={
                "message_type": message_type,
                "error": error
            }
        )

@pytest.mark.asyncio
async def test_calculate_failure_rate(monitoring_service, db_session):
    """Test failure rate calculation."""
    webhook_id = 1
    recent_metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 1.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 1.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = recent_metrics
    failure_rate = await monitoring_service.calculate_failure_rate(webhook_id)
    assert failure_rate == 1/3

@pytest.mark.asyncio
async def test_calculate_failure_rate_no_metrics(monitoring_service, db_session):
    """Test failure rate calculation with no metrics."""
    webhook_id = 1
    db_session.query.return_value.filter.return_value.all.return_value = []
    failure_rate = await monitoring_service.calculate_failure_rate(webhook_id)
    assert failure_rate == 0.0

@pytest.mark.asyncio
async def test_calculate_failure_rate_all_success(monitoring_service, db_session):
    """Test failure rate calculation with all successful deliveries."""
    webhook_id = 1
    recent_metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 1.0),
        make_webhook_metric(webhook_id, "delivery_success", 1.0),
        make_webhook_metric(webhook_id, "delivery_success", 1.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = recent_metrics
    failure_rate = await monitoring_service.calculate_failure_rate(webhook_id)
    assert failure_rate == 0.0

@pytest.mark.asyncio
async def test_calculate_failure_rate_all_failure(monitoring_service, db_session):
    """Test failure rate calculation with all failed deliveries."""
    webhook_id = 1
    recent_metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = recent_metrics
    failure_rate = await monitoring_service.calculate_failure_rate(webhook_id)
    assert failure_rate == 1.0

@pytest.mark.asyncio
async def test_check_alert_conditions(monitoring_service, db_session):
    """Test alert condition checking."""
    webhook_id = 1
    recent_metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = recent_metrics
    dummy_alert = make_alert(AlertType.HIGH_FAILURE_RATE, AlertSeverity.ERROR, "dummy")
    mock_create_alert = AsyncMock(return_value=dummy_alert)
    with patch.object(monitoring_service, '_create_alert', new=mock_create_alert):
        await monitoring_service.check_alert_conditions(webhook_id)
        mock_create_alert.assert_awaited_once()
        alert_args = mock_create_alert.call_args[1]
        assert alert_args['alert_type'] == AlertType.HIGH_FAILURE_RATE
        assert alert_args['severity'] == AlertSeverity.ERROR

@pytest.mark.asyncio
async def test_check_alert_conditions_no_alert(monitoring_service, db_session):
    """Test alert condition checking when no alert is needed."""
    webhook_id = 1
    recent_metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 1.0),
        make_webhook_metric(webhook_id, "delivery_success", 1.0),
        make_webhook_metric(webhook_id, "delivery_success", 1.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = recent_metrics
    with patch.object(monitoring_service, '_create_alert', new=AsyncMock()) as mock_create_alert:
        await monitoring_service.check_alert_conditions(webhook_id)
        mock_create_alert.assert_not_called()

@pytest.mark.asyncio
async def test_check_alert_conditions_cooldown(monitoring_service, db_session):
    """Test alert condition checking with cooldown."""
    webhook_id = 1
    recent_metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = recent_metrics
    
    # Set up cooldown
    alert_key = f"{AlertType.HIGH_FAILURE_RATE}_{AlertSeverity.ERROR}"
    monitoring_service._alert_cooldowns[alert_key] = datetime.now(timezone.utc)
    
    with patch.object(monitoring_service, '_create_alert', new=AsyncMock()) as mock_create_alert:
        await monitoring_service.check_alert_conditions(webhook_id)
        mock_create_alert.assert_not_called()

@pytest.mark.asyncio
async def test_send_notification(monitoring_service):
    """Test notification sending."""
    alert = make_alert(
        alert_type=AlertType.HIGH_FAILURE_RATE,
        severity=AlertSeverity.CRITICAL,
        message="Test alert",
        alert_metadata={"metric": "failure_rate", "value": 0.5},
        created_at=datetime.now(timezone.utc)
    )
    
    # Mock aiohttp.ClientSession
    mock_response = AsyncMock()
    mock_response.__aenter__.return_value.post = AsyncMock()
    
    with patch('aiohttp.ClientSession', return_value=mock_response):
        await monitoring_service._send_notifications(alert)
        
        # Verify webhook notification was sent
        if monitoring_service.alert_config.webhook_url:
            mock_response.__aenter__.return_value.post.assert_any_call(
                monitoring_service.alert_config.webhook_url,
                json={
                    "title": f"Alert: {alert.alert_type.value}",
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "alert_metadata": alert.alert_metadata,
                    "timestamp": alert.created_at.isoformat()
                },
                timeout=5
            )
        
        # Verify Slack notification was sent
        if monitoring_service.alert_config.slack_webhook_url:
            mock_response.__aenter__.return_value.post.assert_any_call(
                monitoring_service.alert_config.slack_webhook_url,
                json={
                    "text": f"*{alert.alert_type.value}*\nSeverity: {alert.severity.value}\n{alert.message}",
                    "attachments": [{
                        "fields": [
                            {"title": k, "value": str(v), "short": True}
                            for k, v in alert.alert_metadata.items()
                        ]
                    }]
                },
                timeout=5
            )

@pytest.mark.asyncio
async def test_get_system_metrics(monitoring_service, db_session):
    """Test system metrics retrieval."""
    metrics = [
        make_system_metric("cpu_usage", 0.5),
        make_system_metric("memory_usage", 0.7)
    ]
    db_session.query.return_value.all.return_value = metrics
    result = await monitoring_service.get_system_metrics()
    assert len(result) == 2
    assert result[0].metric_name == "cpu_usage"
    assert result[1].metric_name == "memory_usage"

@pytest.mark.asyncio
async def test_get_system_metrics_no_metrics(monitoring_service, db_session):
    """Test getting system metrics when no metrics are available."""
    # Mock empty query results
    mock_webhook_metrics = Mock()
    mock_webhook_metrics.total_deliveries = 0
    mock_webhook_metrics.successful_deliveries = 0
    mock_webhook_metrics.avg_response_time = 0
    
    mock_message_metrics = Mock()
    mock_message_metrics.total_messages = 0
    mock_message_metrics.delivered_messages = 0
    mock_message_metrics.avg_processing_time = 0
    
    mock_alert_metrics = Mock()
    mock_alert_metrics.total_alerts = 0
    mock_alert_metrics.error_alerts = 0
    mock_alert_metrics.warning_alerts = 0
    
    # Set up the query chain
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_webhook_metrics,
        mock_message_metrics,
        mock_alert_metrics
    ]
    
    metrics = await monitoring_service.get_system_metrics()
    assert isinstance(metrics, dict)
    assert metrics["webhook_metrics"]["total_deliveries"] == 0
    assert metrics["webhook_metrics"]["success_rate"] == 0
    assert metrics["message_metrics"]["total_messages"] == 0
    assert metrics["message_metrics"]["delivery_rate"] == 0
    assert metrics["alert_metrics"]["total_alerts"] == 0

@pytest.mark.asyncio
async def test_get_webhook_metrics(monitoring_service, db_session):
    """Test webhook metrics retrieval."""
    webhook_id = 1
    metrics = [
        make_webhook_metric(webhook_id, "delivery_success", 1.0),
        make_webhook_metric(webhook_id, "delivery_success", 0.0)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = metrics
    result = await monitoring_service.get_webhook_metrics(webhook_id)
    assert len(result) == 2
    assert result[0].webhook_id == webhook_id
    assert result[1].webhook_id == webhook_id

@pytest.mark.asyncio
async def test_get_webhook_metrics_no_metrics(monitoring_service, db_session):
    """Test webhook metrics retrieval with no metrics."""
    webhook_id = 1
    db_session.query.return_value.filter.return_value.all.return_value = []
    result = await monitoring_service.get_webhook_metrics(webhook_id)
    assert isinstance(result, list)
    assert len(result) == 0

def test_update_alert_status(monitoring_service, db_session):
    """Test alert status update."""
    alert = make_alert(
        alert_type=AlertType.HIGH_FAILURE_RATE,
        severity=AlertSeverity.CRITICAL,
        message="Test alert",
        is_resolved=False
    )
    def commit_side_effect(*args, **kwargs):
        print(f'\ndb.commit called! id(self)={id(db_session)} Stack trace:')
        traceback.print_stack()
        if commit_side_effect.called:
            print('\ndb.commit called more than once! Stack trace:')
            traceback.print_stack()
        commit_side_effect.called = True
    commit_side_effect.called = False
    db_session.commit.side_effect = commit_side_effect
    labels_mock = Mock()
    labels_mock.inc = Mock()
    labels_mock.dec = Mock()
    with patch('services.monitoring_service.ACTIVE_ALERTS.labels', return_value=labels_mock):
        db_session.commit.reset_mock()
        monitoring_service.update_alert_status(alert, True)
    assert alert.is_resolved is True
    db_session.commit.assert_called_once()

def test_get_active_alerts(monitoring_service, db_session):
    """Test active alerts retrieval."""
    alerts = [
        make_alert(AlertType.HIGH_FAILURE_RATE, AlertSeverity.CRITICAL, "Alert 1", is_resolved=False),
        make_alert(AlertType.HIGH_LATENCY, AlertSeverity.ERROR, "Alert 2", is_resolved=False)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = alerts
    result = monitoring_service.get_active_alerts()
    assert len(result) == 2
    assert all(not alert.is_resolved for alert in result)

def test_get_alert_history(monitoring_service, db_session):
    """Test alert history retrieval."""
    alerts = [
        make_alert(AlertType.HIGH_FAILURE_RATE, AlertSeverity.CRITICAL, "Alert 1", is_resolved=True),
        make_alert(AlertType.HIGH_LATENCY, AlertSeverity.ERROR, "Alert 2", is_resolved=True)
    ]
    db_session.query.return_value.filter.return_value.all.return_value = alerts
    result = monitoring_service.get_alert_history()
    assert len(result) == 2
    assert all(alert.is_resolved for alert in result)

def make_webhook_metric(webhook_id, metric_name, metric_value, metric_labels=None):
    from database.models import WebhookMetric
    return WebhookMetric(
        webhook_id=webhook_id,
        metric_name=metric_name,
        metric_value=metric_value,
        metric_labels=metric_labels or {},
    )

def make_system_metric(metric_name, metric_value, metric_labels=None):
    from database.models import SystemMetric
    return SystemMetric(
        metric_name=metric_name,
        metric_value=metric_value,
        metric_labels=metric_labels or {},
    )

def make_alert(alert_type, severity, message, alert_metadata=None, is_resolved=False, created_at=None):
    from database.models import Alert
    return Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        alert_metadata=alert_metadata or {},
        is_resolved=is_resolved,
        created_at=created_at or datetime.now(timezone.utc)
    ) 