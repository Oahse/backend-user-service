#!/bin/bash

# Do not exit on errors
set +e

# Define colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"

info() {
  echo -e "${BLUE}[INFO]${RESET} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${RESET} $1"
}

error() {
  echo -e "${RED}[ERROR]${RESET} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${RESET} $1"
}

# Determine OS type
OS="$(uname -s)"

start_redis() {
  info "Step 5: Starting Redis..."
  if [[ "$OS" == "Darwin" ]]; then
    if command -v brew &> /dev/null; then
      brew services start redis && success "Redis started (macOS)"
    else
      error "Homebrew not found. Please install Redis manually."
    fi
  elif [[ "$OS" == "Linux" ]]; then
    if command -v systemctl &> /dev/null; then
      sudo systemctl start redis && success "Redis started (Linux)"
    else
      error "systemctl not available. Please start Redis manually."
    fi
  else
    error "Unsupported OS: $OS"
  fi
}

check_redis() {
  info "Step 6: Checking Redis status..."
  if redis-cli ping | grep -q "PONG"; then
    success "Redis is running"
  else
    error "Redis is not responding. Please check the Redis service."
  fi
}

info "Step 1: Making migration script executable..."
chmod +x ./run_migrations.sh && success "Migration script made executable"

info "Step 2: Running migration script..."
./run_migrations.sh

info "Step 3: Autogenerating and applying DB migrations..."
alembic revision --autogenerate -m "Migration message" && success "Migration revision created"
alembic upgrade head && success "Database upgraded"

start_redis
sleep 2
check_redis

info "Step 7: Starting Celery worker..."
celery -A tasks.celery_app worker --loglevel=info &
CELERY_PID=$!
success "Celery started with PID $CELERY_PID"

info "Step 8: Starting FastAPI server..."
uvicorn main:app --reload &
UVICORN_PID=$!
success "FastAPI started with PID $UVICORN_PID"

info "All services started. Press Ctrl+C to stop."

# Trap Ctrl+C to stop background jobs
trap "warn 'Stopping servers...'; kill $CELERY_PID $UVICORN_PID; exit" SIGINT SIGTERM

# Wait for both processes
wait
