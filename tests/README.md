# Tests

This directory contains all test files for the application.

## Directory Structure

- `test_api/`: API endpoint tests
  - `test_error_handler.py`: Error handling middleware tests
  - `test_linkedin_api.py`: LinkedIn API endpoint tests
  - `test_twitter_api.py`: Twitter API endpoint tests

- `test_services/`: Service implementation tests
  - `test_monitoring_service.py`: Monitoring service tests
  - `test_social_service.py`: Social media service tests
  - `test_scoring_service.py`: Prospect scoring service tests
  - `test_cache_service.py`: Caching service tests
  - `test_logging_service.py`: Logging service tests

- `test_tasks/`: Celery task tests
  - `test_scoring_tasks.py`: Prospect scoring task tests
  - `test_ab_testing_tasks.py`: A/B testing task tests
  - `test_outreach_tasks.py`: Outreach task tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_services/test_monitoring_service.py

# Run tests with coverage
pytest --cov=app

# Run tests with verbose output
pytest -v
```

## Test Organization

1. Each test file corresponds to a specific module
2. Tests are organized by functionality
3. Fixtures are defined at the module level
4. Mock objects are used for external dependencies

## Best Practices

1. Write descriptive test names
2. Use fixtures for common setup
3. Mock external services and APIs
4. Test both success and failure cases
5. Keep tests focused and isolated
6. Use appropriate assertions
7. Clean up resources after tests

## Structure

- `unit/`: Unit tests
- `integration/`: Integration tests
- `e2e/`: End-to-end tests
- `monitoring/`: Monitoring and performance tests
- `coverage/`: Test coverage reports
- `pytest.ini`: Pytest configuration

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests only
pytest tests/e2e/
```

### With Coverage
```bash
pytest --cov=.
```

## Test Configuration

The `pytest.ini` file configures:
- Test discovery patterns
- Logging levels
- Coverage settings
- Test markers

## Monitoring Tests

The `monitoring/` directory contains:
- Performance tests
- Load tests
- System health checks
- Resource usage monitoring

## Coverage Reports

Coverage reports are generated in `coverage/` and include:
- Line coverage
- Branch coverage
- Missing lines
- Coverage trends