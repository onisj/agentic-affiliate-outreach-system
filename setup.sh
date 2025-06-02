#!/bin/bash
# setup.sh

echo "Setting up Agentic Affiliate Outreach System..."

# Check for Python 3.11
if ! python3 --version | grep -q "3.11"; then
    echo "Python 3.11 is required"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please configure it with your API keys."
fi

# Initialize database
echo "Running database migrations..."
alembic upgrade head

echo "Setup complete! Run './run_dev.sh' to start the development environment."