# Agentic Affiliate Outreach System

An autonomous system for discovering, engaging, and managing affiliate prospects via email, Twitter, and LinkedIn. Built with FastAPI, PostgreSQL, Redis, Celery, and Gradio.


## Project Structure

```python
affiliate_outreach_system/
.
├── alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 0001_initial.py
│       ├── 0002_add_content_table.py
│       ├── 0003_add_sequence_table.py
│       ├── 0004_add_ab_test_tables.py
│       └── 0005_add_sequence_endpoint.py
├── alembic.ini
├── api
│   ├── __init__.py
│   ├── dependencies.py
│   ├── endpoints
│   │   ├── __init__.py
│   │   ├── ab_testing.py
│   │   ├── affiliate_discovery.py
│   │   ├── campaigns.py
│   │   ├── message_templates.py
│   │   ├── monitoring.py
│   │   ├── prospects.py
│   │   ├── responses.py
│   │   ├── templates.py
│   │   └── webhooks.py
│   ├── main.py
│   ├── middleware
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   └── metrics.py
│   ├── routers
│   │   ├── __init__.py
│   │   ├── ab_tests.py
│   │   ├── campaigns.py
│   │   ├── content.py
│   │   ├── health.py
│   │   ├── prospects.py
│   │   ├── sequences.py
│   │   ├── social.py
│   │   ├── templates.py
│   │   └── webhooks.py
│   └── schemas
│       ├── __init__.py
│       ├── campaigns.py
│       ├── content.py
│       ├── prospect.py
│       ├── sequence.py
│       └── template.py
├── awscliv2.zip
├── config
│   ├── __init__.py
│   ├── grafana_dashboard.json
│   ├── grafana_health_dashboard.json
│   ├── grafana_notification_channels.yml
│   ├── prometheus_rules.yml
│   ├── prometheus.yml
│   └── settings.py
├── database
│   ├── __init__.py
│   ├── base.py
│   ├── models.py
│   └── session.py
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── api.md
│   ├── setup.md
│   └── system_design.md
├── error.log
├── LICENSE
├── logging_config.py
├── migrations
│   ├── __init__.py
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 0e9ca861c07f_add_updated_at_to_message_templates.py
│       ├── 565d5aabeb74_add_lead_source_to_affiliateprospect.py
│       ├── a0022ed1f0f4_initial_models.py
│       ├── add_metadata_to_message_logs.py
│       ├── add_monitoring_tables.py
│       ├── c13e97c678ac_add_updated_at_to_message_templates.py
│       ├── ce6cb9564b24_initial_schema.py
│       ├── d5b01d21423f_add_updated_at_to_message_templates.py
│       └── e47db7712763_add_external_message_id_to_message_logs.py
├── monitoring
│   └── prometheus.yml
├── nginx.conf
├── project_structure.txt
├── pytest_errors.log
├── pytest.ini
├── README.md
├── requirements.txt
├── run_dev.sh
├── scripts
│   ├── __init__.py
│   ├── create_tables.py
│   ├── drop_tables.py
│   ├── run_ab_test.py
│   ├── run_prospect_scoring.py
│   └── seed_db.py
├── services
│   ├── __init__.py
│   ├── ab_testing.py
│   ├── affiliate_discovery.py
│   ├── cache_service.py
│   ├── cache.py
│   ├── email_service.py
│   ├── email.py
│   ├── lead_discovery.py
│   ├── linkedin.py
│   ├── logging_service.py
│   ├── messaging.py
│   ├── monitoring_service.py
│   ├── outreach.py
│   ├── prospect_scoring.py
│   ├── response_tracking.py
│   ├── scoring_service.py
│   ├── scrapers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── linkedin.py
│   │   └── twitter.py
│   ├── social_service.py
│   ├── twitter.py
│   ├── validator.py
│   ├── visualization_service.py
│   └── webhook_service.py
├── setup.sh
├── tasks
│   ├── __init__.py
│   ├── celery_app.py
│   ├── outreach_tasks.py
│   ├── response_handler.py
│   ├── scoring_tasks.py
│   └── sequence_tasks.py
├── templates
│   ├── follow_up_email.html
│   ├── sign_up.html
│   └── welcome_email.html
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── load
│   │   ├── __init__.py
│   │   └── locustfile.py
│   ├── test_api
│   │   ├── __init__.py
│   │   ├── test_campaigns.py
│   │   ├── test_content.py
│   │   ├── test_error_handler.py
│   │   ├── test_prospects.py
│   │   └── test_templates.py
│   ├── test_services
│   │   ├── __init__.py
│   │   ├── test_cache_service.py
│   │   ├── test_email_service.py
│   │   ├── test_logging_service.py
│   │   ├── test_monitoring_service.py
│   │   ├── test_scoring_service.py
│   │   ├── test_social_service.py
│   │   └── test_validator.py
│   └── test_tasks
│       ├── __init__.py
│       ├── test_outreach_tasks.py
│       ├── test_response_handler.py
│       ├── test_scoring_tasks.py
│       └── test_sequence_tasks.py
└── ui
    ├── __init__.py
    ├── gradio_app.py
    └── streamlit_app.py
```

## Features
- Autonomous affiliate discovery using Twitter and LinkedIn APIs
- Multi-channel outreach (email, Twitter, LinkedIn)
- Personalized messaging with Jinja2 templates
- Response tracking with NLP-based follow-ups
- GDPR-compliant data storage
- Admin dashboard via Gradio

## Quick Start
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd affiliate_outreach_system
   ```
2. Set up environment variables in `.env` (see `docs/setup.md`).
3. Run with Docker:
   ```bash
   docker-compose up --build
   ```
4. Access:
   - API: `http://localhost:8000/docs`
   - Gradio: `http://localhost:7860`

## Documentation
- [System Design](docs/system_design.md)
- [API Documentation](docs/api.md)
- [Setup Instructions](docs/setup.md)

## Testing
```bash
pytest tests/
```

## License
MIT
