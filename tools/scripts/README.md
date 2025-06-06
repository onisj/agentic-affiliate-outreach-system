# Scripts

This directory contains utility scripts for development, setup, and maintenance.

## Contents

- `setup.sh`: Initial project setup script
- `run_dev.sh`: Development server startup script

## Usage

### Setup Script

The setup script initializes the development environment:

```bash
./scripts/setup.sh
```

This script:
1. Creates a Python virtual environment
2. Installs dependencies
3. Sets up the database
4. Configures environment variables

### Development Script

The development script starts the development server:

```bash
./scripts/run_dev.sh
```

This script:
1. Activates the virtual environment
2. Starts the development server
3. Launches Celery workers
4. Initializes monitoring services

## Adding New Scripts

When adding new scripts:
1. Make them executable: `chmod +x script.sh`
2. Add proper error handling
3. Include usage documentation in the script header
4. Update this README with the new script's purpose and usage 