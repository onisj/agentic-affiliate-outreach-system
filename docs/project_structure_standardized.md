# Standardized Project Structure

## Overview

The Agentic Affiliate Outreach System has been reorganized according to software engineering best practices and clean architecture principles. This document outlines the new standardized structure.

## 🏗️ Root Directory Structure

```
affiliate_outreach_system/
├── src/                          # Source code (Clean Architecture)
│   ├── core/                     # Core business logic
│   ├── services/                 # Microservices
│   ├── shared/                   # Shared components
│   ├── api/                      # API layer
│   └── web/                      # Web interfaces
├── tests/                        # Test suite
├── docs/                         # Documentation
├── data/                         # Data management
├── deployment/                   # Deployment configurations
├── monitoring/                   # Monitoring and observability
├── tools/                        # Development tools and utilities
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── alembic.ini                   # Database migration config
├── LICENSE                       # License file
├── pyproject.toml               # Python project configuration
├── pytest.ini                   # Test configuration
├── README.md                     # Project documentation
└── requirements.txt              # Python dependencies
```

## 📁 Detailed Directory Structure

### `/src` - Source Code (Clean Architecture)

```
src/
├── __init__.py
├── core/                         # Core Domain & Application Layer
│   ├── __init__.py
│   ├── domain/                   # Domain models and business rules
│   ├── application/              # Application services and use cases
│   └── infrastructure/           # Infrastructure concerns
│       ├── database/             # Database models and repositories
│       └── config/               # Configuration management
├── services/                     # Microservices (Domain Services)
│   ├── __init__.py
│   ├── discovery/                # Multi-Platform Discovery Engine
│   ├── intelligence/             # Agentic Intelligence Framework
│   ├── outreach/                 # Dynamic Outreach Orchestration
│   └── analytics/                # Analytics and Intelligence Service
├── shared/                       # Shared Components
│   ├── __init__.py
│   ├── models/                   # Common data models
│   ├── utils/                    # Utility functions
│   └── exceptions/               # Custom exceptions
├── api/                          # API Layer (Interface Adapters)
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── dependencies.py          # API dependencies
│   ├── endpoints/                # API endpoints
│   ├── middleware/               # API middleware
│   ├── routers/                  # API routers
│   └── schemas/                  # Request/Response schemas
└── web/                          # Web Interfaces
    └── frontend/                 # Frontend application
```

### `/tests` - Test Suite

```
tests/
├── __init__.py
├── conftest.py                   # Test configuration
├── pytest.ini                   # Pytest settings
├── utils.py                      # Test utilities
├── test_api/                     # API tests
├── test_services/                # Service tests
├── test_tasks/                   # Task tests
├── load/                         # Load testing
├── monitoring/                   # Monitoring tests
└── coverage/                     # Coverage reports
```

### `/data` - Data Management

```
data/
├── migrations/                   # Database migrations
│   └── alembic/                  # Alembic migration files
├── seeds/                        # Database seed data
│   ├── create_tables.py
│   ├── drop_tables.py
│   └── seed_db.py
└── backups/                      # Database backups
```

### `/deployment` - Deployment Configurations

```
deployment/
├── __init__.py
├── docker/                       # Docker configurations
│   ├── Dockerfile.services       # Multi-stage Dockerfile
│   ├── docker-compose.yml        # Docker Compose
│   └── Dockerfile                # Legacy Dockerfile
├── k8s/                          # Kubernetes manifests
│   └── namespace.yaml            # K8s namespace configuration
└── terraform/                    # Infrastructure as Code
```

### `/monitoring` - Monitoring & Observability

```
monitoring/
├── grafana/                      # Grafana dashboards
│   ├── grafana_dashboard.json
│   ├── grafana_health_dashboard.json
│   └── grafana_notification_channels.yml
├── prometheus/                   # Prometheus configuration
│   ├── prometheus.yml
│   └── prometheus_rules.yml
├── alerting/                     # Alerting rules
└── reports/                      # Generated reports
    └── visualizations/
```

### `/tools` - Development Tools

```
tools/
├── scripts/                      # Development scripts
│   ├── __init__.py
│   ├── config.py
│   ├── README.md
│   ├── run_celery_local.sh
│   ├── run_dev.sh
│   ├── run_tests.sh
│   ├── setup.sh
│   ├── update_imports.py
│   ├── linkedin/                 # LinkedIn-specific tools
│   └── twitter/                  # Twitter-specific tools
├── aws/                          # AWS CLI and tools
└── monitoring/                   # Monitoring tools
```

## 🎯 Architecture Principles Applied

### 1. Clean Architecture

- **Separation of Concerns**: Clear boundaries between layers
- **Dependency Inversion**: Core business logic independent of frameworks
- **Single Responsibility**: Each module has a single, well-defined purpose

### 2. Domain-Driven Design (DDD)

- **Domain Layer**: Pure business logic and rules
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External concerns (database, APIs, etc.)
- **Interface Layer**: Controllers, presenters, and gateways

### 3. Microservices Architecture

- **Service Boundaries**: Clear separation of business capabilities
- **Independent Deployment**: Each service can be deployed independently
- **Technology Diversity**: Services can use different technologies as needed

### 4. Event-Driven Architecture

- **Event Sourcing**: All state changes captured as events
- **CQRS**: Command Query Responsibility Segregation
- **Asynchronous Communication**: Services communicate via events

## 📋 Key Benefits of This Structure

### 1. **Maintainability**

- Clear separation of concerns
- Easy to locate and modify code
- Reduced coupling between components

### 2. **Scalability**

- Independent service scaling
- Clear boundaries for team ownership
- Easy to add new features

### 3. **Testability**

- Isolated business logic
- Clear dependency injection points
- Comprehensive test organization

### 4. **Developer Experience**

- Intuitive directory structure
- Clear naming conventions
- Consistent patterns across services

### 5. **Operational Excellence**

- Clear deployment boundaries
- Comprehensive monitoring setup
- Standardized tooling

## 🔄 Migration Impact

### Files Moved

- `api/` → `src/api/`
- `app/` → `src/core/application/`
- `database/` → `src/core/infrastructure/database/`
- `config/` → `src/core/infrastructure/config/`
- `services/` → `src/services/`
- `shared/` → `src/shared/`
- `frontend/` → `src/web/frontend/`
- `infrastructure/` → `deployment/`
- `deploy/` → `deployment/docker/`
- `scripts/` → `tools/scripts/`
- `utils/` → `src/shared/`
- `alembic/` → `data/migrations/alembic/`
- `reports/` → `monitoring/reports/`
- `htmlcov/` → `tests/coverage/`

### Configuration Updates Needed

1. **Import paths** in Python files
2. **Docker build contexts** in deployment files
3. **Alembic configuration** for new migration path
4. **Test discovery paths** in pytest configuration
5. **CI/CD pipeline paths** in GitHub Actions

## 🚀 Next Steps

1. **Update Import Statements**: Modify Python imports to reflect new structure
2. **Update Configuration Files**: Adjust paths in configuration files
3. **Update Documentation**: Reflect new structure in all documentation
4. **Update CI/CD**: Modify build and deployment scripts
5. **Team Communication**: Inform team of new structure and conventions

## 📖 Standards Compliance

This structure follows:

- **Python Package Standards** (PEP 8, PEP 518)
- **Clean Architecture Principles** (Robert C. Martin)
- **Domain-Driven Design** (Eric Evans)
- **Microservices Patterns** (Chris Richardson)
- **12-Factor App Methodology**
- **Cloud Native Computing Foundation** guidelines

The reorganized structure provides a solid foundation for building, maintaining, and scaling the Agentic Affiliate Outreach System according to industry best practices.
