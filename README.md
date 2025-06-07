# Agentic Affiliate Outreach System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Overview

The **Agentic Affiliate Outreach System** is an autonomous AI-powered platform that revolutionizes affiliate marketing through intelligent prospect discovery, personalized outreach campaigns, and automated relationship management across multiple social media platforms.

### Key Features

- 🤖 **Autonomous AI Agent**: Self-directed decision-making with minimal human intervention
- 🔍 **Multi-Platform Discovery**: Intelligent prospect discovery across LinkedIn, Twitter, YouTube, TikTok, Instagram, and Reddit
- 📧 **Dynamic Outreach**: AI-powered personalization with optimal timing and multi-channel delivery
- 📊 **Real-time Analytics**: Comprehensive performance tracking and predictive insights
- 🔄 **Event-Driven Architecture**: Scalable microservices with CQRS and event sourcing
- 🛡️ **Security & Compliance**: GDPR-compliant with ethical AI practices

## 🏗️ Architecture

This system follows **Clean Architecture** principles with a **microservices** approach:

```
src/
├── core/                 # Core business logic and domain models
├── services/             # Autonomous microservices
├── shared/               # Shared components and utilities
├── api/                  # RESTful API layer
└── web/                  # Web interfaces and frontend
```

### Core Services

- **Discovery Service**: Multi-platform prospect discovery and analysis
- **Intelligence Service**: Autonomous AI agent for decision-making
- **Outreach Service**: Campaign orchestration and message delivery
- **Analytics Service**: Performance tracking and business intelligence

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/affiliate-outreach-system.git
   cd affiliate-outreach-system
   ```

2. **Set up virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**

   ```bash
   alembic upgrade head
   python data/seeds/seed_db.py
   ```

6. **Start the application**

   ```bash
   # Start API server
   python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start Celery worker (in another terminal)
   celery -A src.core.application.tasks.celery_app worker --loglevel=info
   ```

### Docker Deployment

```bash
# Build and start all services
docker-compose -f deployment/docker/docker-compose.yml up -d

# View logs
docker-compose logs -f
```

## 📖 Documentation

- [**Architecture Guide**](docs/system_design.md) - Comprehensive system architecture
- [**API Documentation**](docs/api.md) - RESTful API reference
- [**Setup Guide**](docs/setup.md) - Detailed installation and configuration
- [**Testing Guide**](docs/testing.md) - Testing strategies and guidelines
- [**Project Structure**](docs/project_structure_standardized.md) - Directory organization

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_api/          # API tests
pytest tests/test_services/     # Service tests
pytest tests/load/              # Load tests
```

## 🔧 Development

### Project Structure

```
affiliate_outreach_system/
├── src/                    # Source code
│   ├── core/              # Core business logic
│   ├── services/          # Microservices
│   ├── shared/            # Shared components
│   ├── api/               # API layer
│   └── web/               # Web interfaces
├── tests/                 # Test suite
├── data/                  # Data management
├── deployment/            # Deployment configurations
├── monitoring/            # Monitoring and observability
├── tools/                 # Development tools
└── docs/                  # Documentation
```

### Development Workflow

1. **Feature Development**: Follow clean architecture patterns
2. **Testing**: Write comprehensive tests for all components
3. **Documentation**: Update relevant README files and docs
4. **Code Quality**: Use black, flake8, and mypy for code quality
5. **Deployment**: Use Docker and Kubernetes for deployment

### Code Style

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 🚀 Deployment

### Local Development

```bash
# Start development server
tools/scripts/run_dev.sh
```

### Production Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f deployment/k8s/

# Deploy with Docker Compose
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Infrastructure as Code

```bash
# Deploy infrastructure with Terraform
cd deployment/terraform/
terraform init
terraform plan
terraform apply
```

## 📊 Monitoring

- **Grafana Dashboards**: `http://localhost:3000`
- **Prometheus Metrics**: `http://localhost:9090`
- **API Health Check**: `http://localhost:8000/health`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow clean architecture principles
- Write comprehensive tests
- Update documentation
- Follow code style guidelines
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/affiliate-outreach-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/affiliate-outreach-system/discussions)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [OpenAI](https://openai.com/) and [LangChain](https://langchain.com/)
- Infrastructure managed with [Docker](https://docker.com/) and [Kubernetes](https://kubernetes.io/)
- Monitoring with [Grafana](https://grafana.com/) and [Prometheus](https://prometheus.io/)

---

**Built with ❤️ for autonomous affiliate marketing**
