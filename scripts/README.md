# Scripts Directory

This directory contains various utility scripts for development, deployment, monitoring, and maintenance of the Affiliate Outreach System.

## Directory Structure

```
scripts/
├── dev/                 # Development scripts
│   ├── run_dev.sh      # Run development server
│   ├── run_tests.sh    # Run test suite
│   ├── setup.sh        # Development environment setup
│   └── run_celery_local.sh  # Run Celery locally
│
├── deployment/         # Deployment scripts
│   ├── aws/           # AWS deployment scripts
│   └── docker/        # Docker deployment scripts
│
├── monitoring/        # Monitoring and metrics scripts
│   ├── prometheus/    # Prometheus configuration
│   └── grafana/       # Grafana dashboards
│
└── utils/            # Utility scripts
    ├── linkedin/     # LinkedIn integration scripts
    ├── twitter/      # Twitter integration scripts
    ├── manage_channels.py  # Channel management
    └── update_imports.py   # Import management
```

## Usage

### Development Scripts

```bash
# Run development server
./scripts/dev/run_dev.sh

# Run tests
./scripts/dev/run_tests.sh

# Setup development environment
./scripts/dev/setup.sh

# Run Celery locally
./scripts/dev/run_celery_local.sh
```

### Utility Scripts

```bash
# Update imports
python scripts/utils/update_imports.py

# Manage channels
python scripts/utils/manage_channels.py
```

### Deployment Scripts

```bash
# AWS deployment
./scripts/deployment/aws/deploy.sh

# Docker deployment
./scripts/deployment/docker/deploy.sh
```

### Monitoring Scripts

```bash
# Start monitoring stack
./scripts/monitoring/start.sh

# Configure Prometheus
./scripts/monitoring/prometheus/configure.sh

# Setup Grafana dashboards
./scripts/monitoring/grafana/setup.sh
```

## Adding New Scripts

When adding new scripts:
1. Place them in the appropriate subdirectory
2. Make them executable (`chmod +x script.sh`)
3. Add documentation in this README
4. Follow the existing naming conventions
5. Include proper error handling and logging 