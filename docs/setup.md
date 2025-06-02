# Setup Instructions

## Prerequisites
- Python 3.11
- Docker and docker-compose (optional for Docker-based setup)
- SendGrid, Twitter, LinkedIn API keys

## Non-Docker Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd affiliate_outreach_system
   ```
2. Run setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. Configure `.env` with API keys and database settings.
4. Start development environment:
   ```bash
   chmod +x run_dev.sh
   ./run_dev.sh
   ```
5. Access UIs:
   - Gradio (Lead Generation & Communication System): `http://localhost:7860`
   - Streamlit (Analytics and Optimization): `http://localhost:8501`

## Docker Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd affiliate_outreach_system
   ```
2. Create and populate `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
3. Build and start services:
   ```bash
   docker-compose up --build
   ```
4. Access services:
   - API: `http://localhost:8000` 
   - Gradio: `http://localhost:7860`
   - Streamlit: `http://localhost:8501`
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000`

## Testing
```bash
pytest tests/
```

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret
- `SENDGRID_API_KEY`, `TWITTER_BEARER_TOKEN`, `LINKEDIN_ACCESS_TOKEN`: API keys
- `POSITIVE_RESPONSE_TEMPLATE_ID`, etc.: UUIDs for response templates