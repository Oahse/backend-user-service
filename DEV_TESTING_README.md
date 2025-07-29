# Development Environment Testing Guide

This guide provides comprehensive testing procedures for the development environment to ensure all components work correctly before production deployment.

## Quick Test

```bash
# Run automated development test
./test_dev_environment.sh
```

## Manual Testing Procedures

### 1. Environment Startup Test

```bash
# Start development environment
./run_docker.sh dev up

# Verify all services are running
docker compose -f docker-compose.dev.yml ps

# Expected output should show all services as "Up" or "healthy"
```

### 2. Service Accessibility Tests

#### Frontend Test
```bash
# Test frontend accessibility
curl -f http://localhost:5173
echo $?  # Should return 0 for success

# Test frontend with browser simulation
curl -H "User-Agent: Mozilla/5.0" http://localhost:5173 | grep -q "<title>"
```

#### Backend API Test
```bash
# Test backend health endpoint
curl -f http://localhost:8000/api/v1/health
echo $?  # Should return 0 for success

# Test API documentation
curl -f http://localhost:8000/docs | grep -q "swagger"

# Test API with JSON response
curl -H "Accept: application/json" http://localhost:8000/api/v1/health | jq .
```

#### Database Test
```bash
# Test database connectivity
docker compose -f docker-compose.dev.yml exec users-db pg_isready -U postgres
echo $?  # Should return 0 for success

# Test database content
docker compose -f docker-compose.dev.yml exec users-db psql -U postgres -d app -c "\dt"

# Test backend database connection
docker compose -f docker-compose.dev.yml exec userservice python -c "
from core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"
```

#### Redis Test
```bash
# Test Redis connectivity
docker compose -f docker-compose.dev.yml exec redis redis-cli ping
echo $?  # Should return 0 for success

# Test Redis from backend
docker compose -f docker-compose.dev.yml exec userservice python -c "
import redis
try:
    r = redis.from_url('redis://redis:6379/0')
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
"
```

### 3. Hot Reloading Tests

#### Frontend Hot Reload Test
```bash
# Make a test change to frontend
echo "console.log('Hot reload test - $(date)');" >> frontend/src/App.jsx

# Wait a moment for reload
sleep 3

# Check if change is reflected (check browser console or network tab)
# Revert the change
git checkout -- frontend/src/App.jsx
```

#### Backend Hot Reload Test
```bash
# Make a test change to backend
echo "# Hot reload test - $(date)" >> backend/main.py

# Wait a moment for reload
sleep 3

# Check backend logs for reload message
docker compose -f docker-compose.dev.yml logs userservice | tail -10

# Revert the change
git checkout -- backend/main.py
```

### 4. API Integration Tests

```bash
# Test user registration (if endpoint exists)
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Test user login (if endpoint exists)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"testpass123"}'

# Test protected endpoint (if exists)
# First get token, then use it
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"testpass123"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/users/me
```

### 5. Celery and Background Tasks Test

```bash
# Check Celery worker status
docker compose -f docker-compose.dev.yml exec celery_worker celery -A tasks inspect active

# Test Flower monitoring interface
curl -f http://localhost:5555
echo $?  # Should return 0 for success

# Test background task (if you have test tasks)
docker compose -f docker-compose.dev.yml exec userservice python -c "
from tasks import test_task
result = test_task.delay('test message')
print(f'Task ID: {result.id}')
"
```

### 6. Volume Mount Tests

```bash
# Test frontend volume mount
echo "test file" > frontend/test_volume.txt
docker compose -f docker-compose.dev.yml exec frontend ls -la /app/test_volume.txt
rm frontend/test_volume.txt

# Test backend volume mount
echo "test file" > backend/test_volume.txt
docker compose -f docker-compose.dev.yml exec userservice ls -la /usr/src/app/test_volume.txt
rm backend/test_volume.txt
```

### 7. Environment Variable Tests

```bash
# Test environment variables are loaded correctly
docker compose -f docker-compose.dev.yml exec userservice env | grep -E "(POSTGRES|REDIS|SECRET)"

# Test database URL construction
docker compose -f docker-compose.dev.yml exec userservice python -c "
import os
print('POSTGRES_SERVER:', os.getenv('POSTGRES_SERVER'))
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
"
```

### 8. Network Connectivity Tests

```bash
# Test service-to-service communication
docker compose -f docker-compose.dev.yml exec userservice ping -c 3 users-db
docker compose -f docker-compose.dev.yml exec userservice ping -c 3 redis
docker compose -f docker-compose.dev.yml exec frontend ping -c 3 userservice
```

### 9. Performance Tests

```bash
# Test API response time
time curl -s http://localhost:8000/api/v1/health > /dev/null

# Test frontend load time
time curl -s http://localhost:5173 > /dev/null

# Test concurrent requests
for i in {1..10}; do
  curl -s http://localhost:8000/api/v1/health &
done
wait
```

### 10. Error Handling Tests

```bash
# Test invalid API endpoint
curl -f http://localhost:8000/api/v1/nonexistent
echo $?  # Should return non-zero (error expected)

# Test database connection with wrong credentials
docker compose -f docker-compose.dev.yml exec userservice python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='users-db',
        database='app',
        user='wrong_user',
        password='wrong_password'
    )
    print('This should not succeed')
except Exception as e:
    print('Expected error:', str(e)[:50])
"
```

## Troubleshooting Development Tests

### Common Test Failures

1. **Service Not Ready**: Wait longer for services to start
   ```bash
   sleep 30  # Wait 30 seconds after startup
   ```

2. **Port Conflicts**: Check if ports are already in use
   ```bash
   lsof -i :5173
   lsof -i :8000
   ```

3. **Volume Mount Issues**: Check file permissions
   ```bash
   sudo chown -R $USER:$USER frontend/ backend/
   ```

4. **Network Issues**: Restart Docker network
   ```bash
   docker network rm webnet
   ./run_docker.sh dev up
   ```

### Test Result Interpretation

- **Exit Code 0**: Test passed
- **Exit Code 1**: Test failed
- **Timeout**: Service not responding (may need more time)
- **Connection Refused**: Service not running or wrong port

### Automated Test Script

Create a comprehensive test script:

```bash
#!/bin/bash
# test_dev_comprehensive.sh

set -e

echo "Starting comprehensive development environment test..."

# Start environment
./run_docker.sh dev up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 30

# Run all tests
echo "Running service accessibility tests..."
curl -f http://localhost:5173 && echo "✓ Frontend OK"
curl -f http://localhost:8000/api/v1/health && echo "✓ Backend OK"
curl -f http://localhost:8000/docs && echo "✓ API Docs OK"
curl -f http://localhost:5555 && echo "✓ Flower OK"

echo "Running database tests..."
docker compose -f docker-compose.dev.yml exec users-db pg_isready -U postgres && echo "✓ Database OK"

echo "Running Redis tests..."
docker compose -f docker-compose.dev.yml exec redis redis-cli ping && echo "✓ Redis OK"

echo "All tests completed successfully!"
```

Make it executable:
```bash
chmod +x test_dev_comprehensive.sh
```

## Continuous Testing

For ongoing development, consider setting up automated testing:

```bash
# Watch for changes and run tests
while inotifywait -e modify frontend/src backend/; do
  echo "Changes detected, running quick tests..."
  curl -s http://localhost:8000/api/v1/health > /dev/null && echo "✓ Backend still responsive"
  curl -s http://localhost:5173 > /dev/null && echo "✓ Frontend still responsive"
done
```

This comprehensive testing approach ensures your development environment is working correctly and helps identify issues early in the development process.