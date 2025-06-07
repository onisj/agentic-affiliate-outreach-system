#!/bin/bash
# run_dev.sh

# Development server script for Affiliate Outreach System

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server &
fi

# Start Celery worker
echo "Starting Celery worker..."
celery -A src.app.tasks.celery_app worker --loglevel=info &

# Start Celery beat
echo "Starting Celery beat..."
celery -A src.app.tasks.celery_app beat --loglevel=info &

# Start FastAPI server
echo "Starting FastAPI server..."
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Cleanup on exit
trap 'kill $(jobs -p)' EXIT