# Database

This directory contains all database-related code, migrations, and scripts.

## Structure

- `models.py`: SQLAlchemy models
- `session.py`: Database session management
- `migrations/`: Database migration scripts
- `scripts/`: Database setup and maintenance scripts

## Usage

### Models

Import models in your code:

```python
from database.models import User, Message, Campaign
```

### Session Management

Use the session manager in your code:

```python
from database.session import get_db

db = get_db()
```

### Migrations

Run migrations using Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

### Database Scripts

The `scripts/` directory contains:

- `create_tables.py`: Initial table creation
- `drop_tables.py`: Table cleanup
- `seed_db.py`: Sample data population

## Configuration

Database configuration is managed through environment variables:

- `DATABASE_URL`: Connection string
- `DATABASE_POOL_SIZE`: Connection pool size
- `DATABASE_MAX_OVERFLOW`: Maximum overflow connections 