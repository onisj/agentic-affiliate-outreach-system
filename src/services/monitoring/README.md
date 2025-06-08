# Monitoring Service

The Monitoring Service provides centralized monitoring, logging, and metrics tracking for the Agentic Affiliate Outreach System. It integrates with Prometheus for metrics collection and Grafana for visualization and alerting.

## Features

### Core Monitoring
- Error logging and tracking
- Performance metrics collection
- Rate limit monitoring
- Resource usage tracking
- Business metrics tracking

### Prometheus Integration
- Custom metrics for system health
- Performance tracking
- Rate limit monitoring
- Resource usage metrics
- Business metrics

### Grafana Integration
- Dashboard management
- Alert rule configuration
- Real-time visualization
- Custom metrics display

## Configuration

The Monitoring Service can be configured through a configuration dictionary:

```python
config = {
    'grafana_url': 'http://grafana:3000',
    'grafana_api_key': 'your-api-key',  # Optional
    'grafana_username': 'admin',        # Optional
    'grafana_password': 'password',     # Optional
    'prometheus_push_gateway': 'http://pushgateway:9091',
    'store_errors': True
}

monitoring = MonitoringService(config)
```

## Usage

### Error Logging
```python
monitoring.log_error(
    error_message="Failed to process prospect",
    error_type="processing_error",
    component="prospect_processor",
    context={"prospect_id": "123"}
)
```

### Metrics Recording
```python
monitoring.record_metric(
    metric_name="prospect_score",
    value=0.85,
    labels={"platform": "linkedin", "score_type": "engagement"}
)
```

### Rate Limit Tracking
```python
monitoring.record_rate_limit(
    platform="linkedin",
    limit_type="api",
    remaining=95,
    reset_time=datetime.utcnow() + timedelta(minutes=15)
)
```

### Grafana Dashboard Management
```python
# Create dashboard
dashboard_data = {
    "title": "System Overview",
    "panels": [...]
}
dashboard_uid = await monitoring.create_grafana_dashboard(dashboard_data)

# Update dashboard
await monitoring.update_grafana_dashboard(dashboard_uid, updated_data)

# Get dashboard
dashboard = await monitoring.get_grafana_dashboard(dashboard_uid)
```

### Alert Management
```python
# Create alert
alert_data = {
    "name": "High Error Rate",
    "conditions": [...]
}
alert_uid = await monitoring.create_grafana_alert(alert_data)

# Get alerts
alerts = await monitoring.get_grafana_alerts()
```

## Metrics

### Error Metrics
- `system_errors_total`: Total number of system errors
- Labels: error_type, component

### Performance Metrics
- `request_duration_seconds`: Request duration
- `processing_time_seconds`: Processing time
- Labels: endpoint, method, operation, component

### Rate Limit Metrics
- `rate_limit_hits_total`: Rate limit hits
- Labels: platform, limit_type

### Resource Metrics
- `memory_usage_bytes`: Memory usage
- `cpu_usage_percent`: CPU usage
- Labels: component

### Business Metrics
- `prospect_score`: Prospect scoring
- `engagement_total`: Engagement metrics
- Labels: platform, score_type, metric_type

## Grafana Dashboards

The service includes several pre-configured dashboards:

1. System Overview
   - Error rates
   - Performance metrics
   - Resource usage

2. Platform Metrics
   - Rate limits
   - API usage
   - Response times

3. Business Metrics
   - Prospect scores
   - Engagement rates
   - Conversion metrics

## Alert Rules

Pre-configured alert rules include:

1. Error Rate Alerts
   - High error rate detection
   - Component-specific error thresholds

2. Performance Alerts
   - Response time thresholds
   - Resource usage limits

3. Business Alerts
   - Score threshold violations
   - Engagement rate drops

## Best Practices

1. Error Logging
   - Always include context
   - Use appropriate error types
   - Specify component names

2. Metrics
   - Use consistent naming
   - Include relevant labels
   - Monitor metric cardinality

3. Grafana
   - Use dashboard variables
   - Implement proper refresh rates
   - Set appropriate alert thresholds

## Contributing

When adding new metrics or dashboards:

1. Follow naming conventions
2. Document new metrics
3. Update README
4. Add appropriate labels
5. Create corresponding Grafana panels 