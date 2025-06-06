# Affiliate Outreach System

A comprehensive system for managing and automating outreach campaigns to prospects, with features for tracking responses, managing templates, and analyzing campaign performance.

## Features

- **Prospect Management**: Track and manage prospect information and outreach status
- **Template Management**: Create and manage outreach message templates
- **Automated Outreach**: Send personalized outreach messages to prospects
- **Response Tracking**: Monitor and analyze prospect responses
- **Campaign Analytics**: Track campaign performance and success metrics
- **API Integration**: Connect with LinkedIn and other social platforms
- **Email Integration**: Send and track emails via SendGrid
- **Redis Caching**: Efficient data caching and task queue management
- **Celery Tasks**: Asynchronous task processing for better performance

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Celery
- **Database**: PostgreSQL
- **Cache**: Redis
- **Email**: SendGrid
- **Social Media**: LinkedIn API, Twitter API
- **Testing**: Pytest
- **Containerization**: Docker

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Docker (optional)
- SendGrid API Key
- LinkedIn API Credentials
- Twitter API Credentials (API Key, API Secret, Access Token, Access Token Secret)

## Quick Start

### Local Development

1. Clone the repository:

    ```python
    git clone https://github.com/yourusername/affiliate_outreach_system.git
    cd affiliate_outreach_system
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

5. Start Redis:

    ```bash
    # Using Homebrew (macOS)
    brew services start redis

    # Or using Docker
    docker run -d -p 6379:6379 redis
    ```

6. Run database migrations:

    ```bash
    alembic upgrade head
    ```

7. Start the application:

    ```bash
    # Start the FastAPI server
    uvicorn api.main:app --reload

    # In a separate terminal, start Celery worker
    ./scripts/run_celery_local.sh
    ```

### Docker Setup

1. Build and start the containers:

    ```bash
    docker-compose up --build
    ```

2. Access the application:

- API: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs>
- Health Check: <http://localhost:8000/health>

## Environment Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and set the following variables:

```bash
# Redis Configuration
REDIS_LOCAL_URL=redis://localhost:6379/0
REDIS_DOCKER_URL=redis://redis:6379/0

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# API Keys
SENDGRID_API_KEY=your_sendgrid_key
LINKEDIN_ACCESS_TOKEN=your_linkedin_token

# JWT Settings
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# Email Settings
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
EMAIL_FROM=noreply@yourdomain.com
```

## Development Workflow

1. **Database Migrations**:

    ```bash
    # Create a new migration
    alembic revision --autogenerate -m "description"

    # Apply migrations
    alembic upgrade head

    # Rollback migration
    alembic downgrade -1
    ```

2. **Running Tests**:

    ```bash
    # Run all tests
    pytest

    # Run specific test file
    pytest tests/test_services/test_cache_service.py

    # Run with verbose output
    pytest -v

    # Run with coverage
    pytest --cov=.
    ```

3. **Code Quality**:

    ```bash
    # Run linter
    flake8

    # Run type checking
    mypy .
    ```

## API Documentation

Once the application is running, you can access:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Project Structure

```markdown
affiliate_outreach_system/
├── alembic/              # Database migrations
├── api/                  # FastAPI application
├── config/              # Configuration files
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── tasks/               # Celery tasks
├── templates/           # HTML templates
├── tests/               # Test files
├── .env.example         # Example environment variables
├── docker-compose.yml   # Docker configuration
└── requirements.txt     # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
