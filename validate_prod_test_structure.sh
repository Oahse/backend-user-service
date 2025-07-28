#!/bin/bash

# Production Test Structure Validation Script
# Validates that all required files and configurations are in place for production testing

set -eo pipefail

# Define color codes
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Test counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_TOTAL=0

# Function to print check status
print_check_status() {
    local status="$1"
    local check_name="$2"
    local details="${3:-}"
    
    ((CHECKS_TOTAL++))
    
    if [[ "$status" == "PASS" ]]; then
        echo -e "${GREEN}✓ PASS${NC} $check_name"
        [[ -n "$details" ]] && echo -e "  ${CYAN}→${NC} $details"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} $check_name"
        [[ -n "$details" ]] && echo -e "  ${RED}→${NC} $details"
        ((CHECKS_FAILED++))
    fi
}

# Function to print section header
print_section() {
    local section_name="$1"
    echo
    echo -e "${BLUE}=== $section_name ===${NC}"
}

echo -e "${CYAN}=== Production Test Structure Validation ===${NC}"
echo -e "${BLUE}Validating production environment test setup${NC}"
echo

# Check 1: Required Files
print_section "Required Files Check"

# Test script
if [[ -f "test_prod_environment.sh" && -x "test_prod_environment.sh" ]]; then
    print_check_status "PASS" "Production test script" "test_prod_environment.sh exists and is executable"
else
    print_check_status "FAIL" "Production test script" "test_prod_environment.sh missing or not executable"
fi

# Docker Compose file
echo "DEBUG: Checking docker-compose.prod.yml..."
if [[ -f "docker-compose.prod.yml" ]]; then
    print_check_status "PASS" "Production Docker Compose file" "docker-compose.prod.yml exists"
else
    print_check_status "FAIL" "Production Docker Compose file" "docker-compose.prod.yml missing"
fi

# Environment file
if [[ -f ".env.production" ]]; then
    print_check_status "PASS" "Production environment file" ".env.production exists"
else
    print_check_status "FAIL" "Production environment file" ".env.production missing"
fi

# nginx configuration
if [[ -f "nginx.prod.conf" ]]; then
    print_check_status "PASS" "nginx production config" "nginx.prod.conf exists"
else
    print_check_status "FAIL" "nginx production config" "nginx.prod.conf missing"
fi

# Run script
if [[ -f "run_docker.sh" && -x "run_docker.sh" ]]; then
    print_check_status "PASS" "Docker run script" "run_docker.sh exists and is executable"
else
    print_check_status "FAIL" "Docker run script" "run_docker.sh missing or not executable"
fi

# Check 2: Docker Configuration Validation
print_section "Docker Configuration Validation"

# Validate Docker Compose syntax
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    if docker compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
        print_check_status "PASS" "Docker Compose syntax" "docker-compose.prod.yml has valid syntax"
    else
        print_check_status "FAIL" "Docker Compose syntax" "docker-compose.prod.yml has syntax errors"
    fi
else
    print_check_status "FAIL" "Docker availability" "Docker not available for syntax validation"
fi

# Check required services in compose file
required_services=("redis" "users-db" "userservice" "celery_worker" "flower" "frontend" "nginx")
for service in "${required_services[@]}"; do
    if grep -q "^  $service:" docker-compose.prod.yml; then
        print_check_status "PASS" "Service: $service" "Service defined in docker-compose.prod.yml"
    else
        print_check_status "FAIL" "Service: $service" "Service missing from docker-compose.prod.yml"
    fi
done

# Check 3: Environment Configuration
print_section "Environment Configuration"

# Check required environment variables
required_env_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_SERVER" "REDIS_URL" "SECRET_KEY" "DOMAIN" "ENVIRONMENT")
for var in "${required_env_vars[@]}"; do
    if grep -q "^${var}=" .env.production; then
        print_check_status "PASS" "Environment variable: $var" "Variable defined in .env.production"
    else
        print_check_status "FAIL" "Environment variable: $var" "Variable missing from .env.production"
    fi
done

# Check production-specific settings
if grep -q "ENVIRONMENT=production" .env.production; then
    print_check_status "PASS" "Production environment flag" "ENVIRONMENT set to production"
else
    print_check_status "FAIL" "Production environment flag" "ENVIRONMENT not set to production"
fi

if grep -q "SSL_ENABLED=true" .env.production; then
    print_check_status "PASS" "SSL enabled flag" "SSL_ENABLED set to true"
else
    print_check_status "FAIL" "SSL enabled flag" "SSL_ENABLED not set to true"
fi

# Check 4: nginx Configuration
print_section "nginx Configuration"

# Check nginx config syntax
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    if docker run --rm -v "$(pwd)/nginx.prod.conf:/etc/nginx/nginx.conf:ro" nginx:alpine nginx -t >/dev/null 2>&1; then
        print_check_status "PASS" "nginx configuration syntax" "nginx.prod.conf has valid syntax"
    else
        print_check_status "FAIL" "nginx configuration syntax" "nginx.prod.conf has syntax errors"
    fi
else
    print_check_status "FAIL" "Docker availability" "Docker not available for nginx syntax validation"
fi

# Check required nginx sections
nginx_sections=("upstream backend" "upstream frontend" "limit_req_zone" "server.*listen 80" "server.*listen 443")
for section in "${nginx_sections[@]}"; do
    if grep -q "$section" nginx.prod.conf; then
        print_check_status "PASS" "nginx section: $section" "Section found in nginx.prod.conf"
    else
        print_check_status "FAIL" "nginx section: $section" "Section missing from nginx.prod.conf"
    fi
done

# Check security headers
security_headers=("Strict-Transport-Security" "X-Frame-Options" "X-XSS-Protection" "X-Content-Type-Options" "Content-Security-Policy")
for header in "${security_headers[@]}"; do
    if grep -q "$header" nginx.prod.conf; then
        print_check_status "PASS" "Security header: $header" "Header configured in nginx.prod.conf"
    else
        print_check_status "FAIL" "Security header: $header" "Header missing from nginx.prod.conf"
    fi
done

# Check 5: Dockerfile Validation
print_section "Dockerfile Validation"

# Check frontend production Dockerfile
if [[ -f "frontend/Dockerfile.prod" ]]; then
    print_check_status "PASS" "Frontend production Dockerfile" "frontend/Dockerfile.prod exists"
else
    print_check_status "FAIL" "Frontend production Dockerfile" "frontend/Dockerfile.prod missing"
fi

# Check backend production Dockerfile
if [[ -f "backend/Dockerfile.prod" ]]; then
    print_check_status "PASS" "Backend production Dockerfile" "backend/Dockerfile.prod exists"
else
    print_check_status "FAIL" "Backend production Dockerfile" "backend/Dockerfile.prod missing"
fi

# Check 6: Directory Structure
print_section "Directory Structure"

# Check nginx directory structure
if [[ -d "nginx" ]]; then
    print_check_status "PASS" "nginx directory" "nginx/ directory exists"
    
    if [[ -d "nginx/ssl" ]]; then
        print_check_status "PASS" "nginx SSL directory" "nginx/ssl/ directory exists"
    else
        print_check_status "FAIL" "nginx SSL directory" "nginx/ssl/ directory missing"
    fi
    
    if [[ -d "nginx/conf.d" ]]; then
        print_check_status "PASS" "nginx config directory" "nginx/conf.d/ directory exists"
    else
        print_check_status "FAIL" "nginx config directory" "nginx/conf.d/ directory missing"
    fi
else
    print_check_status "FAIL" "nginx directory" "nginx/ directory missing"
fi

# Check backend scripts
backend_scripts=("backend/entrypoint.prod.sh" "backend/wait-for-it.sh")
for script in "${backend_scripts[@]}"; do
    if [[ -f "$script" && -x "$script" ]]; then
        print_check_status "PASS" "Backend script: $(basename $script)" "$script exists and is executable"
    else
        print_check_status "FAIL" "Backend script: $(basename $script)" "$script missing or not executable"
    fi
done

# Check 7: Test Script Validation
print_section "Test Script Validation"

# Check test script functions
test_functions=("test_prerequisites" "test_environment_startup" "test_nginx_reverse_proxy" "test_ssl_configuration" "test_api_routing" "test_static_file_serving" "test_security_headers" "test_rate_limiting")
for func in "${test_functions[@]}"; do
    if grep -q "^$func()" test_prod_environment.sh; then
        print_check_status "PASS" "Test function: $func" "Function defined in test script"
    else
        print_check_status "FAIL" "Test function: $func" "Function missing from test script"
    fi
done

# Check test endpoints
test_endpoints=("NGINX_HTTP_URL" "NGINX_HTTPS_URL" "API_BASE_URL" "NGINX_HEALTH_URL")
for endpoint in "${test_endpoints[@]}"; do
    if grep -q "readonly $endpoint=" test_prod_environment.sh; then
        print_check_status "PASS" "Test endpoint: $endpoint" "Endpoint defined in test script"
    else
        print_check_status "FAIL" "Test endpoint: $endpoint" "Endpoint missing from test script"
    fi
done

# Print summary
echo
echo -e "${CYAN}=== Validation Summary ===${NC}"
echo -e "Total Checks: $CHECKS_TOTAL"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"

if [[ $CHECKS_FAILED -eq 0 ]]; then
    echo
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    echo -e "${BLUE}Production environment is ready for testing.${NC}"
    echo
    echo -e "${YELLOW}To run production tests:${NC}"
    echo -e "  ./test_prod_environment.sh"
    exit 0
else
    echo
    echo -e "${RED}✗ Some validation checks failed!${NC}"
    echo -e "${YELLOW}Please fix the issues above before running production tests.${NC}"
    exit 1
fi