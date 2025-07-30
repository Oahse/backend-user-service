#!/bin/bash
# Exit immediately if a command exits with a non-zero status or error
set -e
# Define colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"

info() { echo -e "${BLUE}[INFO]${RESET} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${RESET} $1"; }
error() { echo -e "${RED}[ERROR]${RESET} $1"; }
warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }

# Wait for users-db to be ready
info "Waiting for users-db to be ready..."
wait-for-it.sh users-db:5432 --timeout=30 --strict -- sh -c 'echo "[INFO] PostgreSQL Database is up"'

# Wait for Redis
info "Waiting for Redis to be ready..."
wait-for-it.sh redis:6379 --timeout=30 --strict -- sh -c 'echo "[INFO] Redis is up"'

info "Making migration script executable..."
chmod +x ./run_migrations.sh && success "Migration script made executable"

info "Running migration script..."
./run_migrations.sh

info "Starting server..."
# Start app with production optimizations
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --access-log \
    --log-level info