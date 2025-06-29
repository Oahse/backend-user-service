#!/bin/bash

echo "Step 1: Starting Redis..."
brew services start redis

# Wait a moment to ensure Redis is up
sleep 2

echo "Checking Redis status..."
redis-cli ping

# Start Celery worker in the background
echo "Step 2: Starting Celery worker..."
celery -A tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

# Start FastAPI app in the background
echo "Step 3: Starting FastAPI server..."
uvicorn main:app --reload &
UVICORN_PID=$!

# Optionally wait and keep script alive
echo "Celery PID: $CELERY_PID"
echo "Uvicorn PID: $UVICORN_PID"
echo "All services started. Press Ctrl+C to stop."

# Wait indefinitely (optional)
wait
