#!/bin/bash
set -e  # Exit on any error

chmod +x ./run_migrations.sh
./run_migrations.sh

alembic revision --autogenerate -m "Migration message"
alembic upgrade head

echo "Step 1: Starting Redis..."
brew services start redis

sleep 2  # Give Redis time to start

echo "Checking Redis status..."
redis-cli ping

echo "Step 2: Starting Celery worker..."
celery -A tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

echo "Step 3: Starting FastAPI server..."
uvicorn main:app --reload &
UVICORN_PID=$!

echo "Celery PID: $CELERY_PID"
echo "Uvicorn PID: $UVICORN_PID"
echo "All services started. Press Ctrl+C to stop."

# Trap Ctrl+C to kill background jobs
trap "echo 'Stopping...'; kill $CELERY_PID $UVICORN_PID; exit" SIGINT SIGTERM

# Wait indefinitely for background processes
wait
