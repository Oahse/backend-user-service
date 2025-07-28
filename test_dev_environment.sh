#!/bin/bash

# Comprehensive Development Environment Testing Script
# Tests development environment startup, hot reloading, service communication, and connectivity

set -euo pipefail

# Define color codes for better output formatting
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Test configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TEST_LOG_FILE="${SCRIPT_DIR}/dev_test_results.log"
readonly COMPOSE_FILE="docker-compose.dev.yml"
readonly ENV_FILE=".env.local"

# Service endpoints
readonly FRONTEND_URL="http://localhost:5173"
readonly BACKEND_URL="http://localhost:8000"
readonly BACKEND_HEALTH_URL="http://localhost:8000/health"
readonly BACKEND_DOCS_URL="http://localhost:8000/docs"
readonly FLOWER_URL="http://localhost:5555"
readonly POSTGRES_HOST="localhost"
readonly POSTGRES_PORT="5432"
readonly REDIS_HOST="localhost"
readonly REDIS_PORT="6379"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to log test results
log_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$result] $test_name: $details" >> "$TEST_LOG_FILE"
}

# Function to print test status
print_test_status() {
    local status="$1"
    local test_name="$2"
    local details="${3:-}"
    
    ((TESTS_TOTAL++))
    
    if [[ "$status" == "PASS" ]]; then
        echo -e "${GREEN}✓ PASS${NC} $test_name"
        [[ -n "$details" ]] && echo -e "  ${CYAN}→${NC} $details"
        ((TESTS_PASSED++))
        log_test_result "$test_name" "PASS" "$details"
    else
        echo -e "${RED}✗ FAIL${NC} $test_name"
        [[ -n "$details" ]] && echo -e "  ${RED}→${NC} $details"
        ((TESTS_FAILED++))
        log_test_result "$test_name" "FAIL" "$details"
    fi
}

# Function to print test section header
print_test_section() {
    local section_name="$1"
    echo
    echo -e "${BLUE}=== $section_name ===${NC}"
}

# Function to print test summary
print_test_summary() {
    echo
    echo -e "${CYAN}=== Test Summary ===${NC}"
    echo -e "Total Tests: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed! ✓${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed! ✗${NC}"
        return 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url="$1"
    local service_name="$2"
    local max_attempts="${3:-30}"
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $service_name to be ready...${NC}"
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}$service_name is ready (attempt $attempt/$max_attempts)${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: $service_name not ready yet...${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}$service_name failed to become ready after $max_attempts attempts${NC}"
    return 1
}

# Function to wait for TCP service
wait_for_tcp_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts="${4:-30}"
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $service_name TCP connection...${NC}"
    
    while [[ $attempt -le $max_attempts ]]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo -e "${GREEN}$service_name TCP connection is ready (attempt $attempt/$max_attempts)${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: $service_name TCP not ready yet...${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}$service_name TCP connection failed after $max_attempts attempts${NC}"
    return 1
}

# Test 1: Prerequisites Check
test_prerequisites() {
    print_test_section "Prerequisites Check"
    
    # Check Docker
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
            print_test_status "PASS" "Docker availability" "Version: $docker_version"
        else
            print_test_status "FAIL" "Docker daemon" "Docker is installed but daemon is not running"
            echo -e "${YELLOW}Please start Docker daemon and try again${NC}"
            return 1
        fi
    else
        print_test_status "FAIL" "Docker installation" "Docker not found - please install Docker"
        echo -e "${YELLOW}Visit: https://docs.docker.com/engine/install/${NC}"
        return 1
    fi
    
    # Check Docker Compose
    if command_exists docker && docker compose version >/dev/null 2>&1; then
        local compose_version=$(docker compose version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        print_test_status "PASS" "Docker Compose availability" "Version: $compose_version"
    elif command_exists docker-compose; then
        local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        print_test_status "PASS" "Docker Compose availability" "Legacy version: $compose_version"
    else
        print_test_status "FAIL" "Docker Compose availability" "Docker Compose not found"
        return 1
    fi
    
    # Check curl
    if command_exists curl; then
        print_test_status "PASS" "curl availability" "Available for HTTP testing"
    else
        print_test_status "FAIL" "curl availability" "curl not found - required for HTTP tests"
        return 1
    fi
    
    # Check netcat
    if command_exists nc; then
        print_test_status "PASS" "netcat availability" "Available for TCP testing"
    else
        print_test_status "FAIL" "netcat availability" "netcat not found - required for TCP tests"
        return 1
    fi
    
    # Check environment file
    if [[ -f "$ENV_FILE" ]]; then
        print_test_status "PASS" "Environment file exists" "$ENV_FILE found"
    else
        print_test_status "FAIL" "Environment file exists" "$ENV_FILE not found"
        return 1
    fi
    
    # Check Docker Compose file
    if [[ -f "$COMPOSE_FILE" ]]; then
        print_test_status "PASS" "Docker Compose file exists" "$COMPOSE_FILE found"
    else
        print_test_status "FAIL" "Docker Compose file exists" "$COMPOSE_FILE not found"
        return 1
    fi
    
    return 0
}

# Test 2: Environment Startup
test_environment_startup() {
    print_test_section "Environment Startup"
    
    # Start development environment
    echo -e "${YELLOW}Starting development environment...${NC}"
    if ./run_docker.sh dev up >/dev/null 2>&1; then
        print_test_status "PASS" "Development environment startup" "Services started successfully"
    else
        print_test_status "FAIL" "Development environment startup" "Failed to start services"
        return 1
    fi
    
    # Wait a bit for services to initialize
    sleep 5
    
    # Check if containers are running
    local running_containers=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l)
    local total_containers=$(docker compose -f "$COMPOSE_FILE" ps --services | wc -l)
    
    if [[ $running_containers -eq $total_containers ]] && [[ $running_containers -gt 0 ]]; then
        print_test_status "PASS" "All containers running" "$running_containers/$total_containers containers are running"
    else
        print_test_status "FAIL" "All containers running" "Only $running_containers/$total_containers containers are running"
        
        # Show container status for debugging
        echo -e "${YELLOW}Container status:${NC}"
        docker compose -f "$COMPOSE_FILE" ps
        return 1
    fi
    
    return 0
}

# Test 3: Service Health Checks
test_service_health() {
    print_test_section "Service Health Checks"
    
    # Test PostgreSQL connection
    if wait_for_tcp_service "$POSTGRES_HOST" "$POSTGRES_PORT" "PostgreSQL" 15; then
        print_test_status "PASS" "PostgreSQL connectivity" "Database is accessible on port $POSTGRES_PORT"
    else
        print_test_status "FAIL" "PostgreSQL connectivity" "Cannot connect to database"
    fi
    
    # Test Redis connection
    if wait_for_tcp_service "$REDIS_HOST" "$REDIS_PORT" "Redis" 15; then
        print_test_status "PASS" "Redis connectivity" "Redis is accessible on port $REDIS_PORT"
    else
        print_test_status "FAIL" "Redis connectivity" "Cannot connect to Redis"
    fi
    
    # Test backend health endpoint
    if wait_for_service "$BACKEND_HEALTH_URL" "Backend Health" 30; then
        local health_response=$(curl -s "$BACKEND_HEALTH_URL" 2>/dev/null || echo "")
        if echo "$health_response" | grep -q '"status":"healthy"'; then
            print_test_status "PASS" "Backend health check" "Backend reports healthy status"
        else
            print_test_status "FAIL" "Backend health check" "Backend health check failed or unhealthy"
        fi
    else
        print_test_status "FAIL" "Backend health endpoint" "Backend health endpoint not accessible"
    fi
    
    # Test frontend accessibility
    if wait_for_service "$FRONTEND_URL" "Frontend" 30; then
        print_test_status "PASS" "Frontend accessibility" "Frontend is accessible on port 5173"
    else
        print_test_status "FAIL" "Frontend accessibility" "Frontend not accessible"
    fi
    
    # Test Flower (Celery monitoring)
    if wait_for_service "$FLOWER_URL" "Flower" 20; then
        print_test_status "PASS" "Flower accessibility" "Celery monitoring is accessible on port 5555"
    else
        print_test_status "FAIL" "Flower accessibility" "Flower not accessible"
    fi
    
    return 0
}

# Test 4: API Connectivity
test_api_connectivity() {
    print_test_section "API Connectivity"
    
    # Test root endpoint
    local root_response=$(curl -s "$BACKEND_URL/" 2>/dev/null || echo "")
    if echo "$root_response" | grep -q '"service":"User Service API"'; then
        print_test_status "PASS" "Backend root endpoint" "API root endpoint responding correctly"
    else
        print_test_status "FAIL" "Backend root endpoint" "API root endpoint not responding correctly"
    fi
    
    # Test API documentation
    if curl -s -f "$BACKEND_DOCS_URL" >/dev/null 2>&1; then
        print_test_status "PASS" "API documentation" "Swagger docs accessible at /docs"
    else
        print_test_status "FAIL" "API documentation" "Swagger docs not accessible"
    fi
    
    # Test CORS headers
    local cors_response=$(curl -s -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: GET" -X OPTIONS "$BACKEND_URL/" 2>/dev/null || echo "")
    if echo "$cors_response" | grep -qi "access-control-allow-origin"; then
        print_test_status "PASS" "CORS configuration" "CORS headers present for frontend origin"
    else
        print_test_status "FAIL" "CORS configuration" "CORS headers missing or incorrect"
    fi
    
    return 0
}

# Test 5: Database Connectivity
test_database_connectivity() {
    print_test_section "Database Connectivity"
    
    # Test database connection through backend
    local health_response=$(curl -s "$BACKEND_HEALTH_URL" 2>/dev/null || echo "")
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        print_test_status "PASS" "Backend-Database connection" "Backend can connect to database"
    else
        print_test_status "FAIL" "Backend-Database connection" "Backend cannot connect to database"
    fi
    
    # Test direct database connection using Docker exec
    if docker exec users-db pg_isready -U postgres -d users_db >/dev/null 2>&1; then
        print_test_status "PASS" "Direct database connection" "Database accepts connections"
    else
        print_test_status "FAIL" "Direct database connection" "Database not accepting connections"
    fi
    
    return 0
}

# Test 6: Redis Connectivity
test_redis_connectivity() {
    print_test_section "Redis Connectivity"
    
    # Test Redis connection through backend health check
    local health_response=$(curl -s "$BACKEND_HEALTH_URL" 2>/dev/null || echo "")
    if echo "$health_response" | grep -q '"redis":"connected"'; then
        print_test_status "PASS" "Backend-Redis connection" "Backend can connect to Redis"
    else
        print_test_status "FAIL" "Backend-Redis connection" "Backend cannot connect to Redis"
    fi
    
    # Test direct Redis connection using Docker exec
    if docker exec redis redis-cli ping | grep -q "PONG"; then
        print_test_status "PASS" "Direct Redis connection" "Redis responds to ping"
    else
        print_test_status "FAIL" "Direct Redis connection" "Redis not responding to ping"
    fi
    
    return 0
}

# Test 7: Hot Reloading Functionality
test_hot_reloading() {
    print_test_section "Hot Reloading Functionality"
    
    # Test backend hot reloading by checking if uvicorn is running with --reload
    local backend_process=$(docker exec userservice ps aux | grep "uvicorn.*--reload" || echo "")
    if [[ -n "$backend_process" ]]; then
        print_test_status "PASS" "Backend hot reloading" "uvicorn running with --reload flag"
    else
        print_test_status "FAIL" "Backend hot reloading" "uvicorn not running with --reload flag"
    fi
    
    # Test frontend hot reloading by checking if Vite dev server is running
    local frontend_process=$(docker exec frontend ps aux | grep "vite.*dev" || echo "")
    if [[ -n "$frontend_process" ]]; then
        print_test_status "PASS" "Frontend hot reloading" "Vite dev server is running"
    else
        print_test_status "FAIL" "Frontend hot reloading" "Vite dev server not detected"
    fi
    
    # Test volume mounts for hot reloading
    local backend_mount=$(docker inspect userservice | grep -o '"Source":"[^"]*backend"' || echo "")
    if [[ -n "$backend_mount" ]]; then
        print_test_status "PASS" "Backend volume mount" "Backend code directory is mounted for hot reloading"
    else
        print_test_status "FAIL" "Backend volume mount" "Backend volume mount not detected"
    fi
    
    local frontend_mount=$(docker inspect frontend | grep -o '"Source":"[^"]*frontend"' || echo "")
    if [[ -n "$frontend_mount" ]]; then
        print_test_status "PASS" "Frontend volume mount" "Frontend code directory is mounted for hot reloading"
    else
        print_test_status "FAIL" "Frontend volume mount" "Frontend volume mount not detected"
    fi
    
    return 0
}

# Test 8: Service Communication
test_service_communication() {
    print_test_section "Service Communication"
    
    # Test backend to database communication
    if docker exec userservice python -c "
import asyncio
import asyncpg
import os

async def test_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_SERVER', 'users-db'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            database=os.getenv('POSTGRES_DB', 'users_db')
        )
        await conn.close()
        print('SUCCESS')
    except Exception as e:
        print(f'ERROR: {e}')

asyncio.run(test_db())
" 2>/dev/null | grep -q "SUCCESS"; then
        print_test_status "PASS" "Backend-Database communication" "Backend can communicate with database"
    else
        print_test_status "FAIL" "Backend-Database communication" "Backend cannot communicate with database"
    fi
    
    # Test backend to Redis communication
    if docker exec userservice python -c "
import asyncio
import redis.asyncio as redis
import os

async def test_redis():
    try:
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))
        await r.ping()
        await r.close()
        print('SUCCESS')
    except Exception as e:
        print(f'ERROR: {e}')

asyncio.run(test_redis())
" 2>/dev/null | grep -q "SUCCESS"; then
        print_test_status "PASS" "Backend-Redis communication" "Backend can communicate with Redis"
    else
        print_test_status "FAIL" "Backend-Redis communication" "Backend cannot communicate with Redis"
    fi
    
    # Test Celery worker to Redis communication
    if docker exec celery_worker python -c "
import os
from celery import Celery

try:
    app = Celery('tasks')
    app.config_from_object({
        'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1'),
        'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2'),
    })
    
    # Test broker connection
    with app.connection() as conn:
        conn.ensure_connection(max_retries=3)
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null | grep -q "SUCCESS"; then
        print_test_status "PASS" "Celery-Redis communication" "Celery worker can communicate with Redis"
    else
        print_test_status "FAIL" "Celery-Redis communication" "Celery worker cannot communicate with Redis"
    fi
    
    return 0
}

# Test 9: Container Resource Usage
test_container_resources() {
    print_test_section "Container Resource Usage"
    
    # Check if containers are using reasonable resources
    local high_cpu_containers=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}" | awk 'NR>1 && $2+0 > 80 {print $1}')
    if [[ -z "$high_cpu_containers" ]]; then
        print_test_status "PASS" "CPU usage check" "No containers using excessive CPU (>80%)"
    else
        print_test_status "FAIL" "CPU usage check" "High CPU usage detected: $high_cpu_containers"
    fi
    
    # Check memory usage
    local high_mem_containers=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemPerc}}" | awk 'NR>1 && $2+0 > 80 {print $1}')
    if [[ -z "$high_mem_containers" ]]; then
        print_test_status "PASS" "Memory usage check" "No containers using excessive memory (>80%)"
    else
        print_test_status "FAIL" "Memory usage check" "High memory usage detected: $high_mem_containers"
    fi
    
    return 0
}

# Test 10: Environment Variables
test_environment_variables() {
    print_test_section "Environment Variables"
    
    # Test backend environment variables
    local backend_env_check=$(docker exec userservice python -c "
import os
required_vars = ['POSTGRES_SERVER', 'REDIS_URL', 'SECRET_KEY', 'CELERY_BROKER_URL']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'MISSING: {missing}')
else:
    print('SUCCESS')
" 2>/dev/null)
    
    if echo "$backend_env_check" | grep -q "SUCCESS"; then
        print_test_status "PASS" "Backend environment variables" "All required environment variables are set"
    else
        print_test_status "FAIL" "Backend environment variables" "Missing variables: $backend_env_check"
    fi
    
    # Test frontend environment variables
    local frontend_env_check=$(docker exec frontend sh -c "env | grep VITE_API_URL" 2>/dev/null || echo "")
    if [[ -n "$frontend_env_check" ]]; then
        print_test_status "PASS" "Frontend environment variables" "Frontend API URL is configured"
    else
        print_test_status "FAIL" "Frontend environment variables" "Frontend API URL not configured"
    fi
    
    return 0
}

# Cleanup function
cleanup_test_environment() {
    echo -e "${YELLOW}Cleaning up test environment...${NC}"
    ./run_docker.sh dev down >/dev/null 2>&1 || true
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Main test execution
main() {
    # Initialize log file
    echo "=== Development Environment Test Started at $(date) ===" > "$TEST_LOG_FILE"
    
    echo -e "${CYAN}=== Development Environment Testing ===${NC}"
    echo -e "${BLUE}Testing comprehensive development environment functionality${NC}"
    echo -e "${BLUE}Log file: $TEST_LOG_FILE${NC}"
    echo
    
    # Set up trap for cleanup on exit
    trap cleanup_test_environment EXIT
    
    # Run all tests
    test_prerequisites || exit 1
    test_environment_startup || exit 1
    test_service_health
    test_api_connectivity
    test_database_connectivity
    test_redis_connectivity
    test_hot_reloading
    test_service_communication
    test_container_resources
    test_environment_variables
    
    # Print final summary
    if print_test_summary; then
        echo -e "${GREEN}Development environment testing completed successfully!${NC}"
        exit 0
    else
        echo -e "${RED}Development environment testing completed with failures!${NC}"
        echo -e "${YELLOW}Check the log file for details: $TEST_LOG_FILE${NC}"
        exit 1
    fi
}

# Run main function
main "$@"