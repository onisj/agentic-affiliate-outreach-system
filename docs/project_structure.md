# Project Structure and Component Descriptions

```
Affiliate_Outreach_System
├── alembic
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       └── 001_initial_migration.py
├── alembic.ini
├── api
│   ├── __init__.py
│   ├── dependencies.py
│   ├── endpoints
│   │   ├── __init__.py
│   │   ├── ab_testing.py
│   │   ├── affiliate_discovery.py
│   │   ├── campaigns.py
│   │   ├── message_templates.py
│   │   ├── monitoring.py
│   │   ├── prospects.py
│   │   ├── responses.py
│   │   ├── templates.py
│   │   └── webhooks.py
│   ├── main.py
│   ├── middleware
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   └── metrics.py
│   ├── routers
│   │   ├── __init__.py
│   │   ├── ab_tests.py
│   │   ├── campaigns.py
│   │   ├── content.py
│   │   ├── health.py
│   │   ├── prospects.py
│   │   ├── sequences.py
│   │   ├── social.py
│   │   ├── templates.py
│   │   └── webhooks.py
│   └── schemas
│       ├── __init__.py
│       ├── campaigns.py
│       ├── content.py
│       ├── prospect.py
│       ├── sequence.py
│       └── template.py
├── app
│   ├── __init__.py
│   ├── README.md
│   ├── services
│   │   ├── __init__.py
│   │   ├── ab_testing.py
│   │   ├── cache_service.py
│   │   ├── email_service.py
│   │   ├── linkedin.py
│   │   ├── logging_service.py
│   │   ├── monitoring_service.py
│   │   ├── monitoring.py
│   │   ├── outreach_service.py
│   │   ├── outreach.py
│   │   ├── prospect_scoring.py
│   │   ├── response_service.py
│   │   ├── response_tracking.py
│   │   ├── scoring_service.py
│   │   ├── scrapers
│   │   ├── social_service.py
│   │   ├── twitter.py
│   │   ├── validator.py
│   │   ├── visualization_service.py
│   │   └── webhook_service.py
│   └── tasks
│       ├── __init__.py
│       ├── ab_testing_tasks.py
│       ├── celery_app.py
│       ├── outreach_tasks.py
│       ├── response_handler.py
│       ├── scoring_tasks.py
│       ├── sequence_tasks.py
│       └── social
├── aws
│   ├── awscliv2.zip
│   ├── dist
│   │   ├── _awscrt.abi3.so
│   │   ├── _cffi_backend.cpython-313-x86_64-linux-gnu.so
│   │   ├── _ruamel_yaml.cpython-313-x86_64-linux-gnu.so
│   │   ├── aws
│   │   ├── aws_completer
│   │   ├── awscli
│   │   ├── base_library.zip
│   │   ├── cryptography
│   │   ├── docutils
│   │   ├── lib-dynload
│   │   ├── libbz2.so.1
│   │   ├── libffi.so.6
│   │   ├── libgcc_s.so.1
│   │   ├── liblzma.so.5
│   │   ├── libpython3.13.so.1.0
│   │   ├── libreadline.so.6
│   │   ├── libsqlite3.so.0
│   │   ├── libtinfo.so.5
│   │   ├── libuuid.so.1
│   │   └── libz.so.1
│   ├── install
│   ├── README.md
│   └── THIRD_PARTY_LICENSES
├── config
│   ├── __init__.py
│   ├── github
│   │   └── workflows
│   ├── grafana_dashboard.json
│   ├── grafana_health_dashboard.json
│   ├── grafana_notification_channels.yml
│   ├── logging_config.py
│   ├── nginx.conf
│   ├── prometheus_rules.yml
│   ├── prometheus.yml
│   ├── README.md
│   └── settings.py
├── database
│   ├── __init__.py
│   ├── base.py
│   ├── migrations
│   │   ├── __init__.py
│   │   ├── env.py
│   │   ├── README
│   │   └── script.py.mako
│   ├── models.py
│   ├── README.md
│   ├── scripts
│   │   ├── create_tables.py
│   │   ├── drop_tables.py
│   │   └── seed_db.py
│   └── session.py
├── deploy
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── README.md
├── docs
│   ├── api.md
│   ├── images
│   │   └── twitter_api.png
│   ├── project_structure.txt
│   ├── README.md
│   ├── setup.md
│   ├── system_design.md
│   ├── templates
│   │   ├── follow_up_email.html
│   │   ├── prospect_signup.html
│   │   └── welcome_email.html
│   └── testing.md
├── frontend
│   ├── jest.config.js
│   ├── package.json
│   ├── public
│   │   ├── index.html
│   │   └── manifest.json
│   ├── python
│   │   ├── __init__.py
│   │   ├── gradio_app.py
│   │   └── streamlit_app.py
│   ├── README.md
│   ├── src
│   │   ├── __mocks__
│   │   ├── App.tsx
│   │   ├── components
│   │   ├── index.tsx
│   │   ├── setupTests.ts
│   │   └── theme.ts
│   └── tsconfig.json
├── LICENSE
├── pyproject.toml
├── pytest_errors.log
├── README.md
├── reports
│   └── visualizations
├── requirements.txt
├── scripts
│   ├── __init__.py
│   ├── config.py
│   ├── linkedin
│   │   ├── campaign_analytics.py
│   │   ├── connection_manager.py
│   │   └── prospect_research.py
│   ├── README.md
│   ├── run_celery_local.sh
│   ├── run_dev.sh
│   ├── run_tests.sh
│   ├── setup.sh
│   ├── twitter
│   │   ├── campaign_analytics.py
│   │   ├── connection_manager.py
│   │   └── prospect_research.py
│   └── update_imports.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── coverage
│   ├── load
│   │   ├── __init__.py
│   │   └── locustfile.py
│   ├── monitoring
│   │   └── prometheus.yml
│   ├── pytest.ini
│   ├── README.md
│   ├── test_api
│   │   ├── __init__.py
│   │   ├── test_campaigns_api.py
│   │   ├── test_campaigns.py
│   │   ├── test_content.py
│   │   ├── test_error_handler.py
│   │   ├── test_linkedin_api.py
│   │   ├── test_prospects_api.py
│   │   ├── test_prospects.py
│   │   ├── test_templates_api.py
│   │   └── test_templates.py
│   ├── test_services
│   │   ├── __init__.py
│   │   ├── test_cache_service.py
│   │   ├── test_email_service.py
│   │   ├── test_logging_service.py
│   │   ├── test_monitoring_service.py
│   │   ├── test_outreach_service.py
│   │   ├── test_scoring_service.py
│   │   ├── test_social_service.py
│   │   └── test_validator.py
│   ├── test_smoke.py
│   ├── test_tasks
│   │   ├── __init__.py
│   │   ├── test_outreach_tasks.py
│   │   ├── test_response_handler.py
│   │   ├── test_scoring_tasks.py
│   │   └── test_sequence_tasks.py
│   └── utils.py
├── utils
    ├── base_script.py
    ├── base_task.py
    └── README.md
```

## Root Directory
The root directory contains configuration files and main project directories.

### Configuration Files
- `alembic.ini`: Configuration file for Alembic database migrations
- `pytest.ini`: Configuration for pytest testing framework
- `requirements.txt`: Python package dependencies
- `pyproject.toml`: Project metadata and build configuration

## Core Directories

### `/alembic`
Database migration management using Alembic.
- `alembic.ini`: Alembic configuration file
- `env.py`: Environment configuration for migrations
- `versions/`: Contains migration version files
  - `001_initial_migration.py`: Initial database schema setup

### `/api`
FastAPI application and API endpoints.
- `main.py`: FastAPI application entry point
- `dependencies.py`: Shared API dependencies and utilities

#### `/api/endpoints`
API endpoint implementations.
- `ab_testing.py`: A/B testing endpoints
- `affiliate_discovery.py`: Prospect discovery endpoints
- `campaigns.py`: Campaign management endpoints
- `message_templates.py`: Message template endpoints
- `monitoring.py`: System monitoring endpoints
- `prospects.py`: Prospect management endpoints
- `responses.py`: Response tracking endpoints
- `templates.py`: Template management endpoints
- `webhooks.py`: Webhook handling endpoints

#### `/api/middleware`
API middleware components.
- `error_handler.py`: Global error handling middleware
- `metrics.py`: API metrics collection middleware

#### `/api/routers`
API route definitions.
- `ab_tests.py`: A/B testing routes
- `campaigns.py`: Campaign routes
- `content.py`: Content management routes
- `health.py`: Health check routes
- `prospects.py`: Prospect routes
- `sequences.py`: Sequence management routes
- `social.py`: Social media integration routes
- `templates.py`: Template routes
- `webhooks.py`: Webhook routes

#### `/api/schemas`
Pydantic models for request/response validation.
- `campaigns.py`: Campaign-related schemas
- `content.py`: Content-related schemas
- `prospect.py`: Prospect-related schemas
- `sequence.py`: Sequence-related schemas
- `template.py`: Template-related schemas

### `/app`
Core application logic and services.

#### `/app/services`
Business logic services.
- `ab_testing.py`: A/B testing service
- `cache_service.py`: Redis caching service
- `email_service.py`: Email sending and tracking service
- `linkedin.py`: LinkedIn API integration
- `logging_service.py`: Application logging service
- `monitoring_service.py`: System monitoring service
- `outreach_service.py`: Outreach campaign service
- `prospect_scoring.py`: Prospect scoring service
- `response_service.py`: Response handling service
- `response_tracking.py`: Response tracking service
- `scoring_service.py`: Scoring algorithm service
- `social_service.py`: Social media integration service
- `twitter.py`: Twitter API integration
- `validator.py`: Data validation service
- `visualization_service.py`: Data visualization service
- `webhook_service.py`: Webhook handling service

#### `/app/tasks`
Celery task definitions.
- `celery_app.py`: Celery application configuration
- `ab_testing_tasks.py`: A/B testing tasks
- `outreach_tasks.py`: Outreach campaign tasks
- `response_handler.py`: Response processing tasks
- `scoring_tasks.py`: Prospect scoring tasks
- `sequence_tasks.py`: Sequence management tasks

### `/config`
Application configuration files.
- `settings.py`: Application settings and environment variables
- `logging_config.py`: Logging configuration
- `nginx.conf`: Nginx web server configuration
- `prometheus.yml`: Prometheus monitoring configuration
- `prometheus_rules.yml`: Prometheus alerting rules
- `grafana_dashboard.json`: Grafana dashboard configuration
- `grafana_notification_channels.yml`: Grafana notification settings

### `/database`
Database models and session management.
- `base.py`: SQLAlchemy base model
- `models.py`: Database model definitions
- `session.py`: Database session management

#### `/database/scripts`
Database management scripts.
- `create_tables.py`: Table creation script
- `drop_tables.py`: Table cleanup script
- `seed_db.py`: Database seeding script

### `/deploy`
Deployment configuration.
- `docker-compose.yml`: Docker Compose configuration
- `Dockerfile`: Docker image definition

### `/docs`
Project documentation.
- `api.md`: API documentation
- `setup.md`: Setup instructions
- `system_design.md`: System architecture documentation
- `testing.md`: Testing documentation
- `templates/`: Email template examples

### `/frontend`
Frontend application.
- `package.json`: Node.js dependencies
- `tsconfig.json`: TypeScript configuration
- `src/`: Source code
  - `components/`: React components
  - `App.tsx`: Main application component
  - `index.tsx`: Application entry point
- `python/`: Python-based frontend alternatives
  - `gradio_app.py`: Gradio interface
  - `streamlit_app.py`: Streamlit interface

### `/tests`
Test suite.
- `conftest.py`: Pytest configuration and fixtures
- `test_api/`: API endpoint tests
- `test_services/`: Service layer tests
- `test_tasks/`: Celery task tests
- `utils.py`: Test utilities and helpers

### `/utils`
Utility functions and helpers.
- `base_script.py`: Base script class for CLI tools
- `config.py`: Configuration utilities

### `/aws`
AWS deployment and configuration.
- `README.md`: AWS setup instructions
- `dist/`: AWS CLI distribution files

### `/scripts`
Utility scripts.
- `run_celery_local.sh`: Local Celery worker script
- `run_prospect_scoring.py`: Prospect scoring script
- `run_ab_test.py`: A/B testing script
- `inspect_tables.py`: Database inspection script
