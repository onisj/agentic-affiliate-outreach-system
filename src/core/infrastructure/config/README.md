# Configuration

This directory contains all configuration files for the application.

## Contents

- `logging_config.py`: Logging configuration and setup
- `github/`: GitHub Actions workflows and configurations
- `nginx.conf`: Nginx web server configuration

## Usage

### Logging Configuration

The logging configuration can be imported and used in any module:

```python
from config.logging_config import setup_logging

logger = setup_logging(__name__)
```

### Nginx Configuration

The Nginx configuration is used in production deployment. To use it:

1. Copy to the Nginx configuration directory:
```bash
sudo cp nginx.conf /etc/nginx/conf.d/affiliate-outreach.conf
```

2. Test the configuration:
```bash
sudo nginx -t
```

3. Reload Nginx:
```bash
sudo nginx -s reload
```

### GitHub Actions

The GitHub Actions workflows in the `github/` directory handle:
- Automated testing
- Deployment
- Code quality checks
- Security scanning 