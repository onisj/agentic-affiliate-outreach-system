#!/bin/bash

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies with UV
uv pip install -r requirements-test.txt

# Run tests with UV
uv run pytest "$@" 