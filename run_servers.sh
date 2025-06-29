#!/bin/bash
set -e  # Exit on any error

chmod +x ./run_migrations.sh
./run_migrations.sh

echo "Step 4: Run the Migration Command and Apply Migration to the Db..."
alembic revision --autogenerate -m "Migration message"
alembic upgrade head

echo "Step 5: Starting Redis..."
brew services start redis

sleep 2  # Give Redis time to start

echo "Step 6: Checking Redis status..."
redis-cli ping

echo "Step 7: Starting Celery worker..."
celery -A tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

echo "Step 8: Starting FastAPI server..."
uvicorn main:app --reload &
UVICORN_PID=$!

echo "Celery PID: $CELERY_PID"
echo "Uvicorn PID: $UVICORN_PID"
echo "All services started. Press Ctrl+C to stop."

# Trap Ctrl+C to kill background jobs
trap "echo 'Stopping...'; kill $CELERY_PID $UVICORN_PID; exit" SIGINT SIGTERM

# Wait indefinitely for background processes
wait
