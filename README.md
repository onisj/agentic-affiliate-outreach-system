# Agentic Affiliate Outreach System

An autonomous system for discovering, engaging, and managing affiliate prospects via email, Twitter, and LinkedIn. Built with FastAPI, PostgreSQL, Redis, Celery, and Gradio.


## Project Structure

```python
affiliate_outreach_system/
├── alembic/                         # Database migrations
│   ├── env.py                       # Alembic configuration
│   ├── script.py.mako               # Migration script template
│   └── versions/                    # Migration scripts
├── api/                             # API-related code
│   ├── __init__.py
│   ├── main.py                      # FastAPI application
│   ├── dependencies.py              # Dependency injection (e.g., JWT, DB)
│   ├── routers/                     # API route modules
│   │   ├── __init__.py
│   │   ├── prospects.py             # Prospect-related endpoints
│   │   ├── templates.py             # Message template endpoints
│   │   ├── campaigns.py             # Campaign endpoints
│   │   ├── health.py                # Health check endpoint
│   |   └── social.py                # Social media outreach endpointss
│   └── schemas/                     # Pydantic models
│       ├── __init__.py
│       ├── prospect.py              # Prospect schemas
│       ├── template.py              # Template schemas
│       └── campaign.py              # Campaign schemas
├── services/                        # Business logic and external integrations
│   ├── __init__.py
│   ├── email_service.py             # Email sending and personalization
│   ├── lead_discovery.py            # Lead discovery logic
│   ├── scoring_service.py           # Lead scoring logic
│   ├── social_service.py            # Social media outreach (e.g., LinkedIn, Twitter)
│   └── validator.py                 # Data validation utilities
├── tasks/                           # Celery tasks
│   ├── __init__.py
│   ├── celery_app.py                # Celery configuration
│   ├── outreach_tasks.py            # Email and social media outreach tasks
|   ├── response_handler.py          # Response handling tasks
│   └── scoring_tasks.py             # Lead scoring tasks
├── database/                        # Database models and utilities
│   ├── __init__.py
│   ├── models.py                    # SQLAlchemy models
│   └── session.py                   # Database session management
├── ui/                              # Gradio frontend
│   ├── __init__.py
│   └── gradio_app.py                # Gradio interface
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── test_api/                    # API endpoint tests
│   │   ├── test_prospects.py
│   │   ├── test_templates.py
│   │   └── test_campaigns.py
│   ├── test_services/               # Service layer tests
│   │   ├── test_email_service.py    # Email sending tests
│   │   ├── test_scoring_service.py  # Lead scoring tests
│   │   ├── test_social_service.py   # Social media tests
│   │   └── test_validator.py
│   └── test_tasks/                  # Celery task tests
│       ├── test_outreach_tasks.py   # Email and social media outreach tests
│       ├── test_response_handler.py # Response handling tests
│       └── test_scoring_tasks.py    # Lead scoring tests
├── config/                          # Configuration files
│   ├── __init__.py
│   └── settings.py                  # Environment variable management
├── static/                          # Static assets for landing pages
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                       # Jinja2 templates for emails
│   ├── welcome_email.html
│   └── follow_up_email.html
├── docs/                            # Documentation
│   ├── api.md                       # API documentation
│   ├── setup.md                     # Setup instructions
│   └── system_design.md             # System design document
├── .env                             # Environment variables
├── requirements.txt                 # Python dependencies
├── README.md                        # Project overview and setup guide
├── docker-compose.yml               # Docker configuration for services
└── Dockerfile                       # Docker image for the application
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
