#!/bin/bash

# Development Environment Test Structure Validation
# Validates that all test components are properly structured without requiring Docker

set -euo pipefail

# Define color codes
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Test configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

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
    else
        echo -e "${RED}✗ FAIL${NC} $test_name"
        [[ -n "$details" ]] && echo -e "  ${RED}→${NC} $details"
        ((TESTS_FAILED++))
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
    echo -e "${CYAN}=== Validation Summary ===${NC}"
    echo -e "Total Validations: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All validations passed! ✓${NC}"
        return 0
    else
        echo -e "${RED}Some validations failed! ✗${NC}"
        return 1
    fi
}

# Validate test script structure
validate_test_script() {
    print_test_section "Test Script Structure Validation"
    
    # Check if test script exists
    if [[ -f "test_dev_environment.sh" ]]; then
        print_test_status "PASS" "Test script exists" "test_dev_environment.sh found"
    else
        print_test_status "FAIL" "Test script exists" "test_dev_environment.sh not found"
        return 1
    fi
    
    # Check if test script is executable
    if [[ -x "test_dev_environment.sh" ]]; then
        print_test_status "PASS" "Test script executable" "Script has execute permissions"
    else
        print_test_status "FAIL" "Test script executable" "Script lacks execute permissions"
    fi
    
    # Check test functions exist
    local required_functions=(
        "test_prerequisites"
        "test_environment_startup"
        "test_service_health"
        "test_api_connectivity"
        "test_database_connectivity"
        "test_redis_connectivity"
        "test_hot_reloading"
        "test_service_communication"
    )
    
    for func in "${required_functions[@]}"; do
        if grep -q "$func()" "test_dev_environment.sh" 2>/dev/null; then
            print_test_status "PASS" "Function: $func" "Test function is defined"
        else
            print_test_status "FAIL" "Function: $func" "Test function is missing"
        fi
    done
    
    return 0
}

# Validate required files
validate_required_files() {
    print_test_section "Required Files Validation"
    
    local required_files=(
        "run_docker.sh"
        "docker-compose.dev.yml"
        ".env.local"
        "backend/main.py"
        "frontend/package.json"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_test_status "PASS" "File: $file" "Required file exists"
        else
            print_test_status "FAIL" "File: $file" "Required file is missing"
        fi
    done
    
    return 0
}

# Validate Docker Compose configuration
validate_docker_compose() {
    print_test_section "Docker Compose Configuration Validation"
    
    if [[ -f "docker-compose.dev.yml" ]]; then
        # Check for required services
        local required_services=(
            "redis"
            "users-db"
            "userservice"
            "celery_worker"
            "flower"
            "frontend"
        )
        
        for service in "${required_services[@]}"; do
            if grep -q "^  $service:" "docker-compose.dev.yml"; then
                print_test_status "PASS" "Service: $service" "Service is defined in compose file"
            else
                print_test_status "FAIL" "Service: $service" "Service is missing from compose file"
            fi
        done
        
        # Check for health checks
        if grep -q "healthcheck:" "docker-compose.dev.yml"; then
            print_test_status "PASS" "Health checks" "Health checks are configured"
        else
            print_test_status "FAIL" "Health checks" "Health checks are missing"
        fi
        
        # Check for volume mounts
        if grep -q "./backend:/usr/src/app" "docker-compose.dev.yml"; then
            print_test_status "PASS" "Backend volume mount" "Backend hot reload volume is configured"
        else
            print_test_status "FAIL" "Backend volume mount" "Backend hot reload volume is missing"
        fi
        
        if grep -q "./frontend:/app" "docker-compose.dev.yml"; then
            print_test_status "PASS" "Frontend volume mount" "Frontend hot reload volume is configured"
        else
            print_test_status "FAIL" "Frontend volume mount" "Frontend hot reload volume is missing"
        fi
    fi
    
    return 0
}

# Validate environment configuration
validate_environment_config() {
    print_test_section "Environment Configuration Validation"
    
    if [[ -f ".env.local" ]]; then
        local required_vars=(
            "POSTGRES_USER"
            "POSTGRES_PASSWORD"
            "POSTGRES_SERVER"
            "REDIS_URL"
            "SECRET_KEY"
            "BACKEND_CORS_ORIGINS"
        )
        
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" ".env.local"; then
                print_test_status "PASS" "Environment var: $var" "Variable is defined"
            else
                print_test_status "FAIL" "Environment var: $var" "Variable is missing"
            fi
        done
        
        # Check Docker service hostnames
        if grep -q "POSTGRES_SERVER=users-db" ".env.local"; then
            print_test_status "PASS" "Database hostname" "Uses Docker service name"
        else
            print_test_status "FAIL" "Database hostname" "Should use Docker service name 'users-db'"
        fi
        
        if grep -q "redis://redis:" ".env.local"; then
            print_test_status "PASS" "Redis hostname" "Uses Docker service name"
        else
            print_test_status "FAIL" "Redis hostname" "Should use Docker service name 'redis'"
        fi
    fi
    
    return 0
}

# Validate backend configuration
validate_backend_config() {
    print_test_section "Backend Configuration Validation"
    
    if [[ -f "backend/main.py" ]]; then
        # Check for health endpoint
        if grep -q "/health" "backend/main.py"; then
            print_test_status "PASS" "Health endpoint" "Health check endpoint is defined"
        else
            print_test_status "FAIL" "Health endpoint" "Health check endpoint is missing"
        fi
        
        # Check for CORS configuration
        if grep -q "CORSMiddleware" "backend/main.py"; then
            print_test_status "PASS" "CORS middleware" "CORS is configured"
        else
            print_test_status "FAIL" "CORS middleware" "CORS middleware is missing"
        fi
        
        # Check for Redis connection
        if grep -q "redis" "backend/main.py"; then
            print_test_status "PASS" "Redis integration" "Redis connection is configured"
        else
            print_test_status "FAIL" "Redis integration" "Redis connection is missing"
        fi
    fi
    
    return 0
}

# Validate frontend configuration
validate_frontend_config() {
    print_test_section "Frontend Configuration Validation"
    
    if [[ -f "frontend/package.json" ]]; then
        # Check for dev script
        if grep -q '"dev".*"vite"' "frontend/package.json"; then
            print_test_status "PASS" "Dev script" "Vite dev script is configured"
        else
            print_test_status "FAIL" "Dev script" "Vite dev script is missing"
        fi
        
        # Check for React
        if grep -q '"react"' "frontend/package.json"; then
            print_test_status "PASS" "React dependency" "React is configured"
        else
            print_test_status "FAIL" "React dependency" "React dependency is missing"
        fi
    fi
    
    # Check for Dockerfile
    if [[ -f "frontend/Dockerfile.dev" ]]; then
        print_test_status "PASS" "Frontend Dockerfile" "Development Dockerfile exists"
    else
        print_test_status "FAIL" "Frontend Dockerfile" "Development Dockerfile is missing"
    fi
    
    return 0
}

# Validate test coverage
validate_test_coverage() {
    print_test_section "Test Coverage Validation"
    
    # Check if all requirements are covered
    local requirements=(
        "8.1.*development.*environment.*startup"
        "8.3.*service.*communication.*API.*connectivity"
        "8.4.*database.*Redis.*connections"
        "8.5.*hot.*reloading.*functionality"
    )
    
    for req in "${requirements[@]}"; do
        if grep -qi "$req" ".kiro/specs/docker-app-restructure/requirements.md" 2>/dev/null; then
            print_test_status "PASS" "Requirement coverage" "Requirement pattern found: ${req//.*/ }"
        else
            print_test_status "FAIL" "Requirement coverage" "Requirement pattern missing: ${req//.*/ }"
        fi
    done
    
    # Check test script covers all areas
    local test_areas=(
        "prerequisites"
        "startup"
        "health"
        "connectivity"
        "database"
        "redis"
        "hot.*reload"
        "communication"
    )
    
    for area in "${test_areas[@]}"; do
        if grep -qi "$area" "test_dev_environment.sh" 2>/dev/null; then
            print_test_status "PASS" "Test area: $area" "Test coverage exists"
        else
            print_test_status "FAIL" "Test area: $area" "Test coverage missing"
        fi
    done
    
    return 0
}

# Main validation function
main() {
    echo -e "${CYAN}=== Development Environment Test Structure Validation ===${NC}"
    echo -e "${BLUE}Validating test implementation without requiring Docker${NC}"
    echo
    
    # Run all validations
    validate_test_script
    validate_required_files
    validate_docker_compose
    validate_environment_config
    validate_backend_config
    validate_frontend_config
    validate_test_coverage
    
    # Print final summary
    if print_test_summary; then
        echo -e "${GREEN}Test structure validation completed successfully!${NC}"
        echo -e "${YELLOW}Note: To run actual tests, ensure Docker is running and execute: ./test_dev_environment.sh${NC}"
        exit 0
    else
        echo -e "${RED}Test structure validation completed with issues!${NC}"
        echo -e "${YELLOW}Please fix the issues above before running actual tests${NC}"
        exit 1
    fi
}

# Run main function
main "$@"