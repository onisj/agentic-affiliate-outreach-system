# Testing Guide

This document provides comprehensive information about testing in the Affiliate Outreach System.

## Test Structure

The test suite is organized into several categories:

- `tests/test_api/`: API endpoint tests
- `tests/test_services/`: Service layer tests
- `tests/test_tasks/`: Celery task tests
- `tests/utils.py`: Test utilities and fixtures

## Running Tests

### Local Development

1. Install test dependencies:

   ```bash
   uv pip install -r requirements-.txt
   ```

2. Run all tests:

   ```bash
   ./scripts/run_tests.sh
   ```

3. Run specific test categories:

   ```bash
   # Run unit tests
   ./scripts/run_tests.sh -m "unit"

   # Run integration tests
   ./scripts/run_tests.sh -m "integration"

   # Run API tests
   ./scripts/run_tests.sh -m "api"

   # Run Twitter API tests
   ./scripts/run_tests.sh -m "twitter"
   ```

### Test Categories

The following test markers are available:

- `unit`: Unit tests
- `integration`: Integration tests
- `api`: API endpoint tests
- `twitter`: Tests using Twitter API
- `linkedin`: Tests using LinkedIn API
- `email`: Tests using email functionality
- `cache`: Tests using Redis caching
- `database`: Tests requiring database access
- `celery`: Tests using Celery tasks
- `mock`: Tests using mocking
- `e2e`: End-to-end tests
- `performance`: Performance tests
- `security`: Security-related tests

## Test Utilities

### Fixtures

Common fixtures are available in `tests/utils.py`:

- `test_client`: FastAPI test client
- `db_session`: Database session
- `redis_client`: Redis client
- `celery_app`: Celery app
- `mock_services`: Mocked external services

### Decorators

- `@with_db_rollback`: Ensures database changes are rolled back
- `@with_redis_cache`: Clears Redis cache before and after tests

### Test Data

Common test data is available in `TestData` class:

- `PROSPECT`: Sample prospect data
- `TEMPLATE`: Sample template data
- `CAMPAIGN`: Sample campaign data
- `TWITTER_USER`: Sample Twitter user data
- `LINKEDIN_PROFILE`: Sample LinkedIn profile data
- `EMAIL_RESPONSE`: Sample email response data

## Writing Tests

### API Tests

```python
@pytest.mark.api
def test_create_prospect(test_client, db_session):
    # Arrange
    prospect_data = TestData.PROSPECT

    # Act
    response = test_client.post("/api/prospects/", json=prospect_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == prospect_data["email"]
```

### Service Tests

```python
@pytest.mark.unit
def test_create_prospect(outreach_service, db_session):
    # Arrange
    prospect_data = TestData.PROSPECT

    # Act
    prospect = outreach_service.create_prospect(prospect_data)

    # Assert
    assert prospect.email == prospect_data["email"]
```

### Task Tests

```python
@pytest.mark.celery
def test_schedule_outreach_task(outreach_service, celery_app):
    # Arrange
    prospect = create_test_prospect(db_session)
    template = create_test_template(db_session)

    # Act
    task = outreach_service.schedule_outreach_task(prospect.id, template.id)

    # Assert
    assert task.status == "SUCCESS"
```

## CI/CD Integration

Tests are automatically run in GitHub Actions on:

- Push to main branch
- Pull requests to main branch

The CI pipeline includes:

1. Unit and integration tests
2. Security checks
3. Performance tests
4. Code coverage reporting

## Best Practices

1. **Test Organization**:
   - Group related tests in classes
   - Use descriptive test names
   - Follow the Arrange-Act-Assert pattern

2. **Test Data**:
   - Use the `TestData` class for common data
   - Create specific test data when needed
   - Clean up test data after tests

3. **Mocking**:
   - Mock external services
   - Use the `mock_services` fixture
   - Avoid mocking internal services

4. **Database**:
   - Use transactions for database tests
   - Clean up database after tests
   - Use the `db_session` fixture

5. **Redis**:
   - Clear Redis cache before and after tests
   - Use the `redis_client` fixture
   - Mock Redis responses when needed

## Troubleshooting

### Common Issues

1. **Database Connection**:
   - Ensure PostgreSQL is running
   - Check database URL in environment variables
   - Verify database user permissions

2. **Redis Connection**:
   - Ensure Redis is running
   - Check Redis URL in environment variables
   - Verify Redis connection settings

3. **Test Failures**:
   - Check test logs in `pytest_errors.log`
   - Verify test data is correct
   - Ensure all dependencies are installed

### Debugging Tests

1. Run tests with verbose output:

   ```bash
   ./scripts/run_tests.sh -v
   ```

2. Run specific test file:

   ```bash
   ./scripts/run_tests.sh tests/test_services/test_outreach_service.py
   ```

3. Run with debugger:

   ```bash
   ./scripts/run_tests.sh --pdb
   ```

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use appropriate test markers
3. Add test data to `TestData` class if needed
4. Update this documentation if necessary