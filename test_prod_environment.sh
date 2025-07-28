#!/bin/bash

# Comprehensive Production Environment Testing Script
# Tests production environment startup, nginx reverse proxy, SSL, API routing, and security

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
readonly TEST_LOG_FILE="${SCRIPT_DIR}/prod_test_results.log"
readonly COMPOSE_FILE="docker-compose.prod.yml"
readonly ENV_FILE=".env.production"

# Service endpoints for production
readonly NGINX_HTTP_URL="http://localhost:80"
readonly NGINX_HTTPS_URL="https://localhost:443"
readonly NGINX_HEALTH_URL="http://localhost:80/health"
readonly API_BASE_URL="http://localhost:80/api/v1"
readonly BACKEND_DIRECT_URL="http://localhost:8000"  # For internal testing
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
        if curl -s -f -k "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}$service_name is ready (attempt $attempt/$max_attempts)${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: $service_name not ready yet...${NC}"
        sleep 3
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
    
    # Start production environment
    echo -e "${YELLOW}Starting production environment...${NC}"
    if ./run_docker.sh prod up >/dev/null 2>&1; then
        print_test_status "PASS" "Production environment startup" "Services started successfully"
    else
        print_test_status "FAIL" "Production environment startup" "Failed to start services"
        return 1
    fi
    
    # Wait a bit for services to initialize
    sleep 10
    
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

# Test 3: nginx Reverse Proxy Functionality
test_nginx_reverse_proxy() {
    print_test_section "nginx Reverse Proxy Functionality"
    
    # Test nginx is running and accessible
    if wait_for_tcp_service "localhost" "80" "nginx HTTP" 20; then
        print_test_status "PASS" "nginx HTTP port accessibility" "nginx is listening on port 80"
    else
        print_test_status "FAIL" "nginx HTTP port accessibility" "nginx not accessible on port 80"
    fi
    
    # Test nginx HTTPS port (even if SSL not configured, should be listening)
    if wait_for_tcp_service "localhost" "443" "nginx HTTPS" 10; then
        print_test_status "PASS" "nginx HTTPS port accessibility" "nginx is listening on port 443"
    else
        print_test_status "FAIL" "nginx HTTPS port accessibility" "nginx not accessible on port 443"
    fi
    
    # Test nginx health endpoint
    if wait_for_service "$NGINX_HEALTH_URL" "nginx Health" 30; then
        print_test_status "PASS" "nginx health endpoint" "nginx health check accessible"
    else
        print_test_status "FAIL" "nginx health endpoint" "nginx health endpoint not accessible"
    fi
    
    # Test nginx configuration syntax
    if docker exec nginx nginx -t >/dev/null 2>&1; then
        print_test_status "PASS" "nginx configuration syntax" "nginx configuration is valid"
    else
        print_test_status "FAIL" "nginx configuration syntax" "nginx configuration has syntax errors"
    fi
    
    return 0
}

# Test 4: SSL Configuration
test_ssl_configuration() {
    print_test_section "SSL Configuration"
    
    # Test SSL certificate files exist (if configured)
    local ssl_cert_exists=false
    local ssl_key_exists=false
    
    if docker exec nginx test -f /etc/letsencrypt/live/banwee.com/fullchain.pem 2>/dev/null; then
        ssl_cert_exists=true
        print_test_status "PASS" "SSL certificate file" "Certificate file exists"
    else
        print_test_status "FAIL" "SSL certificate file" "Certificate file not found (expected for testing)"
    fi
    
    if docker exec nginx test -f /etc/letsencrypt/live/banwee.com/privkey.pem 2>/dev/null; then
        ssl_key_exists=true
        print_test_status "PASS" "SSL private key file" "Private key file exists"
    else
        print_test_status "FAIL" "SSL private key file" "Private key file not found (expected for testing)"
    fi
    
    # Test HTTPS redirect (should redirect HTTP to HTTPS)
    local redirect_response=$(curl -s -I -L "$NGINX_HTTP_URL" 2>/dev/null | head -1 || echo "")
    if echo "$redirect_response" | grep -q "301\|302"; then
        print_test_status "PASS" "HTTP to HTTPS redirect" "HTTP requests are redirected to HTTPS"
    else
        print_test_status "FAIL" "HTTP to HTTPS redirect" "HTTP to HTTPS redirect not working"
    fi
    
    # Test SSL protocols and ciphers (if SSL is configured)
    if [[ "$ssl_cert_exists" == true && "$ssl_key_exists" == true ]]; then
        if command_exists openssl; then
            local ssl_test=$(echo | openssl s_client -connect localhost:443 -servername banwee.com 2>/dev/null | grep "Protocol\|Cipher" || echo "")
            if [[ -n "$ssl_test" ]]; then
                print_test_status "PASS" "SSL protocol test" "SSL connection successful"
            else
                print_test_status "FAIL" "SSL protocol test" "SSL connection failed"
            fi
        else
            print_test_status "FAIL" "SSL protocol test" "openssl not available for testing"
        fi
    else
        print_test_status "PASS" "SSL protocol test" "Skipped - SSL certificates not configured (expected for testing)"
    fi
    
    return 0
}

# Test 5: API Routing Through nginx
test_api_routing() {
    print_test_section "API Routing Through nginx"
    
    # Test API root endpoint through nginx
    local api_response=$(curl -s "$API_BASE_URL/" 2>/dev/null || echo "")
    if echo "$api_response" | grep -q '"service":"User Service API"'; then
        print_test_status "PASS" "API root endpoint via nginx" "API accessible through nginx reverse proxy"
    else
        print_test_status "FAIL" "API root endpoint via nginx" "API not accessible through nginx"
    fi
    
    # Test API health endpoint through nginx
    local health_response=$(curl -s "$API_BASE_URL/health" 2>/dev/null || echo "")
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        print_test_status "PASS" "API health endpoint via nginx" "Health endpoint accessible through nginx"
    else
        print_test_status "FAIL" "API health endpoint via nginx" "Health endpoint not accessible through nginx"
    fi
    
    # Test API documentation through nginx
    if curl -s -f "$API_BASE_URL/docs" >/dev/null 2>&1; then
        print_test_status "PASS" "API documentation via nginx" "Swagger docs accessible through nginx"
    else
        print_test_status "FAIL" "API documentation via nginx" "Swagger docs not accessible through nginx"
    fi
    
    # Test API response headers
    local api_headers=$(curl -s -I "$API_BASE_URL/" 2>/dev/null || echo "")
    if echo "$api_headers" | grep -qi "content-type.*application/json"; then
        print_test_status "PASS" "API response headers" "Correct content-type headers present"
    else
        print_test_status "FAIL" "API response headers" "Incorrect or missing content-type headers"
    fi
    
    return 0
}

# Test 6: Static File Serving
test_static_file_serving() {
    print_test_section "Static File Serving"
    
    # Test frontend accessibility through nginx
    local frontend_response=$(curl -s -I "$NGINX_HTTP_URL/" 2>/dev/null || echo "")
    if echo "$frontend_response" | grep -q "200 OK"; then
        print_test_status "PASS" "Frontend accessibility via nginx" "Frontend accessible through nginx"
    else
        print_test_status "FAIL" "Frontend accessibility via nginx" "Frontend not accessible through nginx"
    fi
    
    # Test static asset caching headers
    local static_headers=$(curl -s -I "$NGINX_HTTP_URL/assets/css/styles.css" 2>/dev/null || echo "")
    if echo "$static_headers" | grep -qi "cache-control"; then
        print_test_status "PASS" "Static asset caching" "Cache headers present for static assets"
    else
        print_test_status "FAIL" "Static asset caching" "Cache headers missing for static assets"
    fi
    
    # Test frontend container health
    if docker exec frontend curl -s -f "http://localhost/health" >/dev/null 2>&1; then
        print_test_status "PASS" "Frontend container health" "Frontend container is healthy"
    else
        print_test_status "FAIL" "Frontend container health" "Frontend container health check failed"
    fi
    
    return 0
}

# Test 7: Security Headers Validation
test_security_headers() {
    print_test_section "Security Headers Validation"
    
    # Get response headers from nginx
    local headers=$(curl -s -I "$NGINX_HTTP_URL/" 2>/dev/null || echo "")
    
    # Test Strict-Transport-Security header
    if echo "$headers" | grep -qi "strict-transport-security"; then
        print_test_status "PASS" "HSTS header" "Strict-Transport-Security header present"
    else
        print_test_status "FAIL" "HSTS header" "Strict-Transport-Security header missing"
    fi
    
    # Test X-Frame-Options header
    if echo "$headers" | grep -qi "x-frame-options"; then
        print_test_status "PASS" "X-Frame-Options header" "X-Frame-Options header present"
    else
        print_test_status "FAIL" "X-Frame-Options header" "X-Frame-Options header missing"
    fi
    
    # Test X-XSS-Protection header
    if echo "$headers" | grep -qi "x-xss-protection"; then
        print_test_status "PASS" "X-XSS-Protection header" "X-XSS-Protection header present"
    else
        print_test_status "FAIL" "X-XSS-Protection header" "X-XSS-Protection header missing"
    fi
    
    # Test X-Content-Type-Options header
    if echo "$headers" | grep -qi "x-content-type-options"; then
        print_test_status "PASS" "X-Content-Type-Options header" "X-Content-Type-Options header present"
    else
        print_test_status "FAIL" "X-Content-Type-Options header" "X-Content-Type-Options header missing"
    fi
    
    # Test Content-Security-Policy header
    if echo "$headers" | grep -qi "content-security-policy"; then
        print_test_status "PASS" "Content-Security-Policy header" "CSP header present"
    else
        print_test_status "FAIL" "Content-Security-Policy header" "CSP header missing"
    fi
    
    # Test Referrer-Policy header
    if echo "$headers" | grep -qi "referrer-policy"; then
        print_test_status "PASS" "Referrer-Policy header" "Referrer-Policy header present"
    else
        print_test_status "FAIL" "Referrer-Policy header" "Referrer-Policy header missing"
    fi
    
    return 0
}

# Test 8: Rate Limiting
test_rate_limiting() {
    print_test_section "Rate Limiting"
    
    # Test API rate limiting by making multiple rapid requests
    local rate_limit_triggered=false
    local success_count=0
    local rate_limit_count=0
    
    echo -e "${YELLOW}Testing API rate limiting (making 25 rapid requests)...${NC}"
    
    for i in {1..25}; do
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/" 2>/dev/null || echo "000")
        if [[ "$response_code" == "200" ]]; then
            ((success_count++))
        elif [[ "$response_code" == "429" ]]; then
            ((rate_limit_count++))
            rate_limit_triggered=true
        fi
        sleep 0.1  # Small delay between requests
    done
    
    if [[ "$rate_limit_triggered" == true ]]; then
        print_test_status "PASS" "API rate limiting" "Rate limiting triggered after $success_count requests ($rate_limit_count rate limited)"
    else
        print_test_status "FAIL" "API rate limiting" "Rate limiting not triggered after 25 requests"
    fi
    
    # Test rate limit headers
    local rate_limit_headers=$(curl -s -I "$API_BASE_URL/" 2>/dev/null || echo "")
    if echo "$rate_limit_headers" | grep -qi "x-ratelimit\|x-rate-limit"; then
        print_test_status "PASS" "Rate limit headers" "Rate limiting headers present"
    else
        print_test_status "FAIL" "Rate limit headers" "Rate limiting headers missing"
    fi
    
    return 0
}

# Test 9: Service Health Checks
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
    
    # Test backend health through nginx
    local health_response=$(curl -s "$NGINX_HEALTH_URL" 2>/dev/null || echo "")
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        print_test_status "PASS" "Backend health via nginx" "Backend reports healthy status through nginx"
    else
        print_test_status "FAIL" "Backend health via nginx" "Backend health check failed through nginx"
    fi
    
    # Test Flower (Celery monitoring)
    if wait_for_service "$FLOWER_URL" "Flower" 20; then
        print_test_status "PASS" "Flower accessibility" "Celery monitoring is accessible on port 5555"
    else
        print_test_status "FAIL" "Flower accessibility" "Flower not accessible"
    fi
    
    return 0
}

# Test 10: Container Resource Usage
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
    
    # Check nginx worker processes
    local nginx_workers=$(docker exec nginx ps aux | grep "nginx: worker" | wc -l)
    if [[ $nginx_workers -gt 0 ]]; then
        print_test_status "PASS" "nginx worker processes" "$nginx_workers nginx worker processes running"
    else
        print_test_status "FAIL" "nginx worker processes" "No nginx worker processes detected"
    fi
    
    return 0
}

# Test 11: Service Communication
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
    
    # Test nginx to backend communication
    local nginx_backend_test=$(docker exec nginx curl -s -f "http://userservice:8000/health" 2>/dev/null || echo "")
    if echo "$nginx_backend_test" | grep -q '"status":"healthy"'; then
        print_test_status "PASS" "nginx-Backend communication" "nginx can communicate with backend"
    else
        print_test_status "FAIL" "nginx-Backend communication" "nginx cannot communicate with backend"
    fi
    
    # Test nginx to frontend communication
    if docker exec nginx curl -s -f "http://frontend:80/" >/dev/null 2>&1; then
        print_test_status "PASS" "nginx-Frontend communication" "nginx can communicate with frontend"
    else
        print_test_status "FAIL" "nginx-Frontend communication" "nginx cannot communicate with frontend"
    fi
    
    return 0
}

# Test 12: Production Environment Variables
test_production_environment_variables() {
    print_test_section "Production Environment Variables"
    
    # Test backend environment variables
    local backend_env_check=$(docker exec userservice python -c "
import os
required_vars = ['POSTGRES_SERVER', 'REDIS_URL', 'SECRET_KEY', 'CELERY_BROKER_URL', 'DOMAIN']
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
    
    # Test production-specific environment variables
    local prod_env_check=$(docker exec userservice python -c "
import os
env = os.getenv('ENVIRONMENT', '')
domain = os.getenv('DOMAIN', '')
ssl_enabled = os.getenv('SSL_ENABLED', 'false')
if env == 'production' and domain and ssl_enabled:
    print('SUCCESS')
else:
    print(f'ERROR: env={env}, domain={domain}, ssl_enabled={ssl_enabled}')
" 2>/dev/null)
    
    if echo "$prod_env_check" | grep -q "SUCCESS"; then
        print_test_status "PASS" "Production-specific variables" "Production environment variables correctly set"
    else
        print_test_status "FAIL" "Production-specific variables" "Production environment variables not set correctly"
    fi
    
    return 0
}

# Cleanup function
cleanup_test_environment() {
    echo -e "${YELLOW}Cleaning up test environment...${NC}"
    ./run_docker.sh prod down >/dev/null 2>&1 || true
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Main test execution
main() {
    # Initialize log file
    echo "=== Production Environment Test Started at $(date) ===" > "$TEST_LOG_FILE"
    
    echo -e "${CYAN}=== Production Environment Testing ===${NC}"
    echo -e "${BLUE}Testing comprehensive production environment functionality${NC}"
    echo -e "${BLUE}Log file: $TEST_LOG_FILE${NC}"
    echo
    
    # Set up trap for cleanup on exit
    trap cleanup_test_environment EXIT
    
    # Run all tests
    test_prerequisites || exit 1
    test_environment_startup || exit 1
    test_nginx_reverse_proxy
    test_ssl_configuration
    test_api_routing
    test_static_file_serving
    test_security_headers
    test_rate_limiting
    test_service_health
    test_container_resources
    test_service_communication
    test_production_environment_variables
    
    # Print final summary
    if print_test_summary; then
        echo -e "${GREEN}Production environment testing completed successfully!${NC}"
        exit 0
    else
        echo -e "${RED}Production environment testing completed with failures!${NC}"
        echo -e "${YELLOW}Check the log file for details: $TEST_LOG_FILE${NC}"
        exit 1
    fi
}

# Run main function
main "$@"