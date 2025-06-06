# Application Core

This directory contains the core application components, including services and tasks.

## Directory Structure

- `services/`: Core business logic and service implementations
  - `monitoring.py`: System monitoring and alerting
  - `social_service.py`: Social media integration
  - `outreach_service.py`: Outreach campaign management
  - `response_service.py`: Response handling and tracking
  - `scoring_service.py`: Prospect scoring and qualification

- `tasks/`: Celery tasks for background processing
  - `scoring_tasks.py`: Prospect scoring tasks
  - `ab_testing_tasks.py`: A/B testing tasks
  - `outreach_tasks.py`: Outreach campaign tasks

## Usage

### Services

Services encapsulate business logic and external integrations:

```python
from app.services.monitoring import MonitoringService
from app.services.social_service import SocialService

# Initialize services
monitoring = MonitoringService()
social = SocialService()

# Use service methods
monitoring.track_webhook_delivery(...)
social.get_linkedin_profile(...)
```

### Tasks

Tasks handle background processing and scheduled jobs:

```python
from app.tasks.scoring_tasks import score_prospect
from app.tasks.ab_testing_tasks import create_ab_test

# Call tasks
score_prospect.delay(prospect_id=123)
create_ab_test.delay(campaign_id=456, ...)
```

## Best Practices

1. Keep services focused on specific domains
2. Use dependency injection for service dependencies
3. Handle errors and logging consistently
4. Document public interfaces
5. Write unit tests for all services and tasks 