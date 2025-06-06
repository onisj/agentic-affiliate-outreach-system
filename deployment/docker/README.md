# Deployment Configuration

This directory contains all deployment-related configuration files and scripts.

## Contents

- `Dockerfile`: Defines the container image for the application
- `docker-compose.yml`: Orchestrates the deployment of multiple services

## Usage

1. Build the container:

```bash
docker build -t affiliate-outreach .
```

2. Start the services:

```bash
docker-compose up -d
```

3. View logs:

```bash
docker-compose logs -f
```

## Services

The deployment includes:

- Web application
- Database
- Redis for caching
- Celery workers
- Monitoring services
