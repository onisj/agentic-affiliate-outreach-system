#!/bin/bash
# run_dev.sh

echo "Starting development environment..."

# Start PostgreSQL and Redis (assuming they're installed locally)
# Alternatively, ensure they're running via Docker or system services

# Start FastAPI server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start Celery worker
celery -A tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

# Start Gradio UI
python ui/gradio_app.py &
GRADIO_PID=$!

# Wait for any process to exit
wait $API_PID $CELERY_PID $GRADIO_PID

# Cleanup
kill $API_PID $CELERY_PID $GRADIO_PID 2>/dev/null