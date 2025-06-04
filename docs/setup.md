# Affiliate Outreach System – Setup Guide

This guide provides comprehensive instructions to set up, configure, and run the Affiliate Outreach System, including the FastAPI backend, Gradio and Streamlit UIs, Celery tasks, Redis, PostgreSQL, and monitoring with Prometheus and Grafana.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Repository Setup](#repository-setup)
- [Non-Docker Setup](#non-docker-setup)
  - [Python Virtual Environment](#python-virtual-environment)
  - [Environment Configuration](#environment-configuration)
  - [Installing Redis Locally](#installing-redis-locally)
  - [Installing Prometheus Locally](#installing-prometheus-locally)
  - [Running Services Manually](#running-services-manually)
- [Docker-Based Setup](#docker-based-setup)
- [Database Migrations with Alembic](#database-migrations-with-alembic)
- [Testing](#testing)
- [Monitoring and Dashboards](#monitoring-and-dashboards)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Production Deployment Notes](#production-deployment-notes)
- [Useful CLI Tools](#useful-cli-tools)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Ensure the following are installed:

- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **pip** and **virtualenv**: `pip install virtualenv`
- **PostgreSQL 15+**: [Installation Guide](https://www.postgresql.org/download/)
- **Redis 7.2+**: Required for Celery task queuing (installed below)
- **Node.js 18+** (optional, for frontend development if applicable)
- **Docker and Docker Compose** (optional, for containerized setup): [Install Docker](https://docs.docker.com/get-docker/)
- **API Credentials**:
  - SendGrid API key
  - Twitter Bearer Token
  - LinkedIn Access Token (OAuth)
- **Git**: For cloning the repository

Verify installations:

```bash
python3 --version
psql --version
redis-cli --version
docker --version
```

## Repository Setup

Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd affiliate_outreach_system
```

## Non-Docker Setup

This section covers setting up the system locally without Docker, as preferred for Redis.

### Python Virtual Environment

Create and activate a virtual environment:

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

If `requirements.txt` is missing, install core dependencies:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis celery prometheus-fastapi-instrumentator streamlit gradio flower alembic pytest
```

### Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
nano .env
```

Populate `.env` with the following (adjust values as needed):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/affiliate_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<random-secure-key>  # Generate with: openssl rand -hex 32
SENDGRID_API_KEY=<your-sendgrid-key>
TWITTER_BEARER_TOKEN=<your-twitter-token>
LINKEDIN_CLIENT_ID=<your-linkedin-client-id>
LINKEDIN_CLIENT_SECRET=<your-linkedin-client-secret>
LINKEDIN_REDIRECT_URL=http://localhost:8000/auth/linkedin/callback
POSITIVE_RESPONSE_TEMPLATE_ID=<uuid>
NEGATIVE_RESPONSE_TEMPLATE_ID=<uuid>
NEUTRAL_RESPONSE_TEMPLATE_ID=<uuid>
```

Create the PostgreSQL database:

```bash
psql -U <user> -c "CREATE DATABASE affiliate_db;"
```

### Installing Redis Locally

Install Redis to support Celery task queuing:

- **Ubuntu/Debian**:
  
  ```bash
  sudo apt-get update
  sudo apt-get install redis-server
  sudo systemctl start redis
  sudo systemctl enable redis
  ```
- **macOS**:
  
  ```bash
  brew install redis
  brew services start redis
  ```
- **Windows** (via WSL2 recommended):
  Install Ubuntu on WSL2 (`wsl --install`), then follow Ubuntu instructions.

Verify Redis:

```bash
redis-cli ping  # Should return "PONG"
```

### Installing Prometheus Locally

Install Prometheus for monitoring:

- **Ubuntu/Debian**:
  
  ```bash
  sudo apt-get install prometheus
  ```
- **macOS**:
  
  ```bash
  brew install prometheus
  ```
- **Windows**: Use WSL2 or download from [prometheus.io](https://prometheus.io/download/).

Create `monitoring/prometheus.yml` (as provided earlier):

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
        labels:
          app: 'affiliate-outreach'
          environment: 'development'
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
        labels:
          app: 'redis'
          environment: 'development'
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:5555']
        labels:
          app: 'celery'
          environment: 'development'
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          app: 'prometheus'
          environment: 'development'
```

Install Redis Exporter:

```bash
# Ubuntu
sudo apt-get install prometheus-redis-exporter
sudo systemctl start prometheus-redis-exporter
# macOS
brew install prometheus-redis-exporter
redis_exporter --redis.addr=localhost:6379
```

Run Prometheus:

```bash
prometheus --config.file=monitoring/prometheus.yml
```

### Running Services Manually

Start each service in a separate terminal:

- **FastAPI**:
  
  ```bash
  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
  ```
  
  URL: <http://localhost:8000>
- **Celery Workers**:
  
  ```bash
  celery -A tasks.celery_app worker --loglevel=info -Q outreach_queue,scoring_queue,response_queue,sequence_queue
  ```
- **Flower (Celery Monitoring)**:
  
  ```bash
  celery -A tasks.celery_app flower --port=5555
  ```
  
  URL: <http://localhost:5555>
- **Gradio UI**:
  
  ```bash
  python ui/gradio_app.py
  ```
  
  URL: <http://localhost:7860>
- **Streamlit UI**:
  
  ```bash
  streamlit run ui/streamlit_app.py
  ```
  
  URL: <http://localhost:8501>
- **Grafana** (optional, via Docker for simplicity):
  
  ```bash
  docker run -d -p 3000:3000 --name grafana grafana/grafana
  ```
  
  URL: <http://localhost:3000> (login: `admin`/`admin`)

Optional: Create a `run_dev.sh` script:

```bash
#!/bin/bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
celery -A tasks.celery_app worker --loglevel=info -Q outreach_queue,scoring_queue,response_queue,sequence_queue &
celery -A tasks.celery_app flower --port=5555 &
python ui/gradio_app.py &
streamlit run ui/streamlit_app.py &
prometheus --config.file=monitoring/prometheus.yml &
```

Run:

```bash
chmod +x run_dev.sh
./run_dev.sh
```

## Docker-Based Setup

For containerized deployment, use Docker Compose.

1. **Configure `.env`**:
   
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Set `REDIS_URL=redis://redis:6379/0` if Redis is Dockerized (see below).
2. **Update `docker-compose.yml`**:
   Ensure it includes Redis, Prometheus, and other services. Example:
   
   ```yaml
   version: '3.8'
   services:
     fastapi:
       build: .
       ports:
         - "8000:8000"
       environment:
         - REDIS_URL=redis://redis:6379/0
         - DATABASE_URL=postgresql://user:password@db:5432/affiliate_db
       depends_on:
         - redis
         - db
       networks:
         - affiliate_network
     redis:
       image: redis:7.2-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       networks:
         - affiliate_network
     db:
       image: postgres:15
       environment:
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=password
         - POSTGRES_DB=affiliate_db
       ports:
         - "5432:5432"
       volumes:
         - db_data:/var/lib/postgresql/data
       networks:
         - affiliate_network
     celery:
       build: .
       command: celery -A tasks.celery_app worker --loglevel=info -Q outreach_queue,scoring_queue,response_queue,sequence_queue
       environment:
         - REDIS_URL=redis://redis:6379/0
       depends_on:
         - redis
       networks:
         - affiliate_network
     flower:
       build: .
       command: celery -A tasks.celery_app flower --port=5555
       ports:
         - "5555:5555"
       depends_on:
         - redis
       networks:
         - affiliate_network
     gradio:
       build: .
       command: python ui/gradio_app.py
       ports:
         - "7860:7860"
       networks:
         - affiliate_network
     streamlit:
       build: .
       command: streamlit run ui/streamlit_app.py
       ports:
         - "8501:8501"
       networks:
         - affiliate_network
     prometheus:
       image: prom/prometheus:v2.54.1
       ports:
         - "9090:9090"
       volumes:
         - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
         - prometheus_data:/prometheus
       networks:
         - affiliate_network
     grafana:
       image: grafana/grafana
       ports:
         - "3000:3000"
       volumes:
         - grafana_data:/var/lib/grafana
       networks:
         - affiliate_network
   volumes:
     redis_data:
     db_data:
     prometheus_data:
     grafana_data:
   networks:
     affiliate_network:
       driver: bridge
   ```
3. **Build and Run**:
   
   ```bash
   docker-compose up --build -d
   ```
   
   Access services at the same URLs as non-Docker setup.

## Database Migrations with Alembic

Apply migrations to set up the database schema:

```bash
alembic upgrade head
```

Create a new migration if models change:

```bash
alembic revision --autogenerate -m "Add new table or column"
```

Troubleshoot migration issues:

- Check `migrations/versions/` for conflicts.
- Verify `DATABASE_URL` in `.env`.

## Testing

Run unit and integration tests:

```bash
pytest tests/ --log-file=pytest_errors.log
```

Ensure services (FastAPI, Redis, PostgreSQL) are running during tests.

## Monitoring and Dashboards

- **Prometheus**: Access at <http://localhost:9090>. Verify targets (`fastapi`, `redis`, etc.) under “Status > Targets”.
- **Grafana**: Access at <http://localhost:3000>. Add Prometheus as a data source (`http://prometheus:9090` in Docker, `http://localhost:9090` locally). Import dashboards:
  - FastAPI: [Grafana Dashboard](https://grafana.com/grafana/dashboards/)
  - Redis: [Dashboard 11835](https://grafana.com/grafana/dashboards/11835)
- **Flower**: Monitor Celery tasks at <http://localhost:5555>.

## Project Structure

```plaintext
affiliate_outreach_system/
├── api/                # FastAPI routers and main app
├── config/             # Settings and configuration
├── database/           # SQLAlchemy models and session
├── migrations/         # Alembic migrations
├── monitoring/         # Prometheus and Grafana configs
├── services/           # Business logic (email, social, scoring)
├── tasks/              # Celery tasks
├── templates/          # Email and UI templates
├── tests/              # Unit and load tests
├── ui/                 # Gradio and Streamlit apps
├── .env.example        # Environment template
├── docker-compose.yml  # Docker orchestration
├── prometheus.yml      # Prometheus configuration
├── requirements.txt    # Python dependencies
├── run_dev.sh          # Development script
```

## Troubleshooting

|Issue                      |Solution                                                      |
|---------------------------|--------------------------------------------------------------|
|Port in use                |`lsof -i :<port>` and `kill -9 <pid>`                         |
|`ModuleNotFoundError`      |Activate virtualenv: `source venv/bin/activate`               |
|Redis connection refused   |Ensure Redis runs: `redis-cli ping`                           |
|Database connection error  |Verify `DATABASE_URL` and PostgreSQL status                   |
|Prometheus targets down    |Check service ports and `promtool check config prometheus.yml`|
|Grafana data not persisting|Mount volume in `docker-compose.yml`                          |
|Celery tasks not running   |Check Redis (`REDIS_URL`) and worker logs                     |

## Security Considerations

- Use strong `SECRET_KEY` and API credentials.
- Restrict Redis to `localhost` (`bind 127.0.0.1` in `redis.conf`).
- Enable HTTPS for production (e.g., via Nginx).
- Rotate API tokens regularly.
- Use environment-specific `.env` files (e.g., `.env.prod`).

## Production Deployment Notes

- Use a managed Redis service (e.g., AWS ElastiCache) for scalability.
- Deploy PostgreSQL on a managed service (e.g., RDS).
- Use a WSGI server (Gunicorn) with Uvicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app`.
- Set up CI/CD with `github_actions.yml` or equivalent.
- Monitor with Prometheus/Grafana and configure alerting rules.

## Useful CLI Tools

- **httpie**: `http :8000/ping`
- **pgcli**: `pgcli -h localhost -U user affiliate_db`
- **redis-cli**: `redis-cli -h localhost`
- **alembic**: `alembic upgrade head`
- **locust**: `locust -f tests/load_test.py`
- **promtool**: `promtool check config prometheus.yml`

## Contributing

Report issues or submit PRs via `issues.md`. Follow contribution guidelines in `CONTRIBUTING.md` if available.

## License

© 2025 Affiliate Outreach System. All rights reserved.
