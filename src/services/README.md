# Services Directory

This directory contains all the core services for the Agentic Affiliate Outreach System. The services are organized into the following categories:

## Discovery Services
Located in `discovery/`, these services handle prospect discovery and analysis:
- `intelligence/`: AI-powered analysis components
- `scrapers/`: Platform-specific data collection
- `pipeline/`: Data processing pipeline
- `orchestrator/`: Task scheduling and coordination

## Monitoring Services
Located in `monitoring/`, these services handle system monitoring and logging:
- Metrics collection
- Error tracking
- Performance monitoring
- Alert management

## Outreach Services
Located in `outreach/`, these services handle prospect outreach:
- Email management
- Social media integration
- Response tracking
- Campaign management

## Analytics Services
Located in `analytics/`, these services handle data analysis:
- Channel analytics
- Campaign performance
- Prospect scoring
- Trend analysis

## Visualization Services
Located in `visualization/`, these services handle data visualization:
- Dashboard generation
- Report creation
- Data presentation
- Interactive visualizations

## Usage

To use these services in your code, import them directly from the services package:

```python
from services.discovery.intelligence import IntelligenceService
from services.monitoring import MonitoringService
from services.outreach import OutreachService
from services.analytics import AnalyticsService
from services.visualization import VisualizationService
```

## Service Dependencies

Services are designed to be modular and can be used independently. However, some services may depend on others:

- All services depend on the MonitoringService for logging and metrics
- Outreach services may depend on Discovery services for prospect data
- Analytics services may depend on both Discovery and Outreach services
- Visualization services depend on Analytics services for data

## Configuration

Each service can be configured through its constructor:

```python
from services.monitoring import MonitoringService

monitoring = MonitoringService(config={
    'log_level': 'INFO',
    'metrics_enabled': True
})
```

## Error Handling

All services implement consistent error handling and logging:

```python
try:
    result = await service.perform_operation()
except Exception as e:
    monitoring.log_error(
        f"Operation failed: {str(e)}",
        error_type="operation_error",
        component="service_name"
    )
    raise
```

## Metrics

Services automatically record metrics for monitoring:

```python
monitoring.record_metric(
    'operation_duration',
    duration,
    {'operation': 'name'}
)
```

## Contributing

When adding new services:
1. Place them in the appropriate subdirectory
2. Update this README with documentation
3. Add necessary tests
4. Ensure proper error handling and metrics
5. Update the service's `__init__.py` to expose public interfaces 