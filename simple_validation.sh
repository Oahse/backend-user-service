#!/bin/bash

echo "=== Simple Production Test Validation ==="

# Check required files
echo "Checking required files..."
[[ -f "test_prod_environment.sh" ]] && echo "✓ test_prod_environment.sh" || echo "✗ test_prod_environment.sh"
[[ -f "docker-compose.prod.yml" ]] && echo "✓ docker-compose.prod.yml" || echo "✗ docker-compose.prod.yml"
[[ -f ".env.production" ]] && echo "✓ .env.production" || echo "✗ .env.production"
[[ -f "nginx.prod.conf" ]] && echo "✓ nginx.prod.conf" || echo "✗ nginx.prod.conf"
[[ -f "run_docker.sh" ]] && echo "✓ run_docker.sh" || echo "✗ run_docker.sh"

# Check executability
echo "Checking script permissions..."
[[ -x "test_prod_environment.sh" ]] && echo "✓ test_prod_environment.sh is executable" || echo "✗ test_prod_environment.sh not executable"
[[ -x "run_docker.sh" ]] && echo "✓ run_docker.sh is executable" || echo "✗ run_docker.sh not executable"

# Check Docker Compose syntax
echo "Checking Docker Compose syntax..."
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    if docker compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
        echo "✓ docker-compose.prod.yml syntax is valid"
    else
        echo "✗ docker-compose.prod.yml has syntax errors"
    fi
else
    echo "⚠ Docker not available for syntax check"
fi

echo "Validation complete!"