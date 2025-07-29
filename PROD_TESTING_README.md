# Production Environment Testing Guide

This guide provides comprehensive testing procedures for the production environment to ensure all components work correctly with nginx reverse proxy, SSL configuration, and optimized builds.

## Quick Test

```bash
# Run automated production test
./test_prod_environment.sh
```

## Manual Testing Procedures

### 1. Environment Startup Test

```bash
# Start production environment
./run_docker.sh prod up

# Verify all services are running
docker compose -f docker-compose.prod.yml ps

# Expected output should show all services as "Up" or "healthy"
# nginx should be running and healthy
```

### 2. nginx Reverse Proxy Tests

#### Frontend Serving Test
```bash
# Test frontend serving through nginx
curl -f http://localhost/
echo $?  # Should return 0 for success

# Test frontend with specific headers
curl -H "Accept: text/html" http://localhost/ | grep -q "<html>"

# Test frontend assets
curl -f http://localhost/assets/index.js
curl -f http://localhost/assets/index.css
```

#### API Proxy Test
```bash
# Test API routing through nginx
curl -f http://localhost/api/v1/health
echo $?  # Should return 0 for success

# Test API with JSON response
curl -H "Accept: application/json" http://localhost/api/v1/health | jq .

# Test API documentation through nginx
curl -f http://localhost/api/v1/docs
```

#### Static File Serving Test
```bash
# Test static file serving with caching headers
curl -I http://localhost/assets/index.js | grep -E "(Cache-Control|ETag|Last-Modified)"

# Test gzip compression
curl -H "Accept-Encoding: gzip" -I http://localhost/ | grep "Content-Encoding: gzip"

# Test different file types
curl -f http://localhost/favicon.ico
curl -f http://localhost/robots.txt
```

### 3. SSL/HTTPS Tests (if configured)

#### SSL Certificate Test
```bash
# Test HTTPS redirect
curl -I http://localhost/ | grep -E "(301|302)"

# Test SSL certificate validity
echo | openssl s_client -connect localhost:443 -servername yourdomain.com 2>/dev/null | openssl x509 -noout -dates

# Test SSL configuration
nmap --script ssl-enum-ciphers -p 443 localhost

# Test SSL certificate chain
echo | openssl s_client -connect localhost:443 -servername yourdomain.com 2>/dev/null | openssl x509 -noout -issuer
```

#### HTTPS Functionality Test
```bash
# Test HTTPS frontend
curl -k https://localhost/
echo $?  # Should return 0 for success

# Test HTTPS API
curl -k https://localhost/api/v1/health
echo $?  # Should return 0 for success

# Test mixed content (should work)
curl -k https://localhost/api/v1/docs
```

### 4. Security Headers Tests

```bash
# Test security headers presence
curl -I http://localhost/ | grep -E "(X-Frame-Options|X-Content-Type-Options|X-XSS-Protection|Strict-Transport-Security)"

# Test specific security headers
echo "Checking security headers:"
response=$(curl -s -I http://localhost/)
echo "$response" | grep "X-Frame-Options" && echo "✓ X-Frame-Options present"
echo "$response" | grep "X-Content-Type-Options" && echo "✓ X-Content-Type-Options present"
echo "$response" | grep "X-XSS-Protection" && echo "✓ X-XSS-Protection present"
echo "$response" | grep "Strict-Transport-Security" && echo "✓ HSTS present"

# Test CORS headers
curl -H "Origin: https://yourdomain.com" -I http://localhost/api/v1/health | grep "Access-Control-Allow-Origin"
```

### 5. Rate Limiting Tests

```bash
# Test API rate limiting
echo "Testing rate limiting (may take a moment)..."
for i in {1..50}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/health)
  if [ "$response" = "429" ]; then
    echo "✓ Rate limiting working - got 429 after $i requests"
    break
  fi
  sleep 0.1
done

# Test rate limiting headers
curl -I http://localhost/api/v1/health | grep -E "(X-RateLimit|Retry-After)"
```

### 6. Performance Tests

#### Response Time Tests
```bash
# Test frontend response time
echo "Testing frontend response time:"
time curl -s http://localhost/ > /dev/null

# Test API response time
echo "Testing API response time:"
time curl -s http://localhost/api/v1/health > /dev/null

# Test static asset response time
echo "Testing static asset response time:"
time curl -s http://localhost/assets/index.js > /dev/null
```

#### Load Tests
```bash
# Simple concurrent request test
echo "Testing concurrent requests..."
for i in {1..20}; do
  curl -s http://localhost/api/v1/health > /dev/null &
done
wait
echo "✓ Concurrent requests completed"

# Test with different endpoints
endpoints=("/" "/api/v1/health" "/api/v1/docs")
for endpoint in "${endpoints[@]}"; do
  echo "Testing endpoint: $endpoint"
  time curl -s "http://localhost$endpoint" > /dev/null
done
```

#### Resource Usage Tests
```bash
# Check container resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check nginx worker processes
docker compose -f docker-compose.prod.yml exec nginx ps aux | grep nginx

# Check backend worker processes
docker compose -f docker-compose.prod.yml exec userservice ps aux | grep python
```

### 7. Database and Redis Tests

```bash
# Test database connectivity in production
docker compose -f docker-compose.prod.yml exec users-db pg_isready -U postgres
echo $?  # Should return 0 for success

# Test Redis connectivity in production
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
echo $?  # Should return 0 for success

# Test backend connections to database and Redis
docker compose -f docker-compose.prod.yml exec userservice python -c "
from core.database import engine
import redis
import os

# Test database
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✓ Database connection OK')
except Exception as e:
    print(f'✗ Database connection failed: {e}')

# Test Redis
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('✓ Redis connection OK')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
"
```

### 8. Celery and Background Tasks Tests

```bash
# Test Celery worker in production
docker compose -f docker-compose.prod.yml exec celery_worker celery -A tasks inspect active

# Test Flower monitoring through nginx
curl -f http://localhost/flower/
echo $?  # Should return 0 for success

# Test background task processing
docker compose -f docker-compose.prod.yml exec userservice python -c "
from tasks import test_task
result = test_task.delay('production test')
print(f'Task ID: {result.id}')
print('Task submitted successfully')
"
```

### 9. nginx Configuration Tests

```bash
# Test nginx configuration syntax
docker compose -f docker-compose.prod.yml exec nginx nginx -t
echo $?  # Should return 0 for success

# Test nginx reload
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Check nginx error logs
docker compose -f docker-compose.prod.yml logs nginx | grep -i error

# Check nginx access logs
docker compose -f docker-compose.prod.yml logs nginx | tail -20
```

### 10. Error Handling Tests

```bash
# Test 404 handling
curl -s -o /dev/null -w "%{http_code}" http://localhost/nonexistent
# Should return 404

# Test API error handling
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/nonexistent
# Should return 404

# Test backend service unavailable
docker compose -f docker-compose.prod.yml stop userservice
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/health
# Should return 502 or 503
docker compose -f docker-compose.prod.yml start userservice

# Wait for service to be ready
sleep 10
curl -f http://localhost/api/v1/health && echo "✓ Service recovered"
```

### 11. Monitoring and Logging Tests

```bash
# Test log aggregation
docker compose -f docker-compose.prod.yml logs --tail=50

# Test specific service logs
docker compose -f docker-compose.prod.yml logs nginx | tail -10
docker compose -f docker-compose.prod.yml logs userservice | tail -10

# Test log rotation (if configured)
docker compose -f docker-compose.prod.yml exec nginx ls -la /var/log/nginx/

# Test health check endpoints
curl http://localhost/api/v1/health | jq .
```

## Advanced Production Tests

### 12. Security Penetration Tests

```bash
# Test for common vulnerabilities
echo "Running basic security tests..."

# Test for directory traversal
curl -s -o /dev/null -w "%{http_code}" "http://localhost/../../../etc/passwd"
# Should return 404 or 403

# Test for SQL injection (basic)
curl -s -o /dev/null -w "%{http_code}" "http://localhost/api/v1/users?id=1' OR '1'='1"
# Should return 400 or 422

# Test for XSS protection
curl -H "User-Agent: <script>alert('xss')</script>" -s -o /dev/null -w "%{http_code}" http://localhost/
# Should return 200 but script should be filtered

# Test for clickjacking protection
curl -I http://localhost/ | grep "X-Frame-Options"
# Should be present
```

### 13. Backup and Recovery Tests

```bash
# Test database backup
docker compose -f docker-compose.prod.yml exec users-db pg_dump -U postgres app > prod_test_backup.sql
echo $?  # Should return 0 for success

# Test backup file
ls -la prod_test_backup.sql
wc -l prod_test_backup.sql

# Clean up test backup
rm prod_test_backup.sql
```

### 14. Scalability Tests

```bash
# Test horizontal scaling (if configured)
docker compose -f docker-compose.prod.yml up --scale userservice=2 -d

# Verify multiple backend instances
docker compose -f docker-compose.prod.yml ps userservice

# Test load balancing
for i in {1..10}; do
  curl -s http://localhost/api/v1/health | jq -r '.hostname // "no-hostname"'
done

# Scale back down
docker compose -f docker-compose.prod.yml up --scale userservice=1 -d
```

## Automated Production Test Script

Create a comprehensive production test script:

```bash
#!/bin/bash
# test_prod_comprehensive.sh

set -e

echo "Starting comprehensive production environment test..."

# Start environment
./run_docker.sh prod up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 60

# Test nginx reverse proxy
echo "Testing nginx reverse proxy..."
curl -f http://localhost/ && echo "✓ Frontend through nginx OK"
curl -f http://localhost/api/v1/health && echo "✓ API through nginx OK"

# Test security headers
echo "Testing security headers..."
curl -I http://localhost/ | grep -q "X-Frame-Options" && echo "✓ Security headers OK"

# Test static file serving
echo "Testing static file serving..."
curl -I http://localhost/assets/ | grep -q "Cache-Control" && echo "✓ Static file caching OK"

# Test database and Redis
echo "Testing database and Redis..."
docker compose -f docker-compose.prod.yml exec users-db pg_isready -U postgres && echo "✓ Database OK"
docker compose -f docker-compose.prod.yml exec redis redis-cli ping && echo "✓ Redis OK"

# Test performance
echo "Testing performance..."
response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/)
echo "Frontend response time: ${response_time}s"

api_response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/api/v1/health)
echo "API response time: ${api_response_time}s"

echo "All production tests completed successfully!"
```

Make it executable:
```bash
chmod +x test_prod_comprehensive.sh
```

## Troubleshooting Production Tests

### Common Production Test Failures

1. **nginx Not Starting**: Check configuration syntax
   ```bash
   docker compose -f docker-compose.prod.yml exec nginx nginx -t
   ```

2. **SSL Certificate Issues**: Verify certificate files
   ```bash
   ls -la nginx/ssl/prod/
   openssl x509 -in nginx/ssl/prod/fullchain.pem -text -noout
   ```

3. **Rate Limiting Too Aggressive**: Adjust nginx configuration
   ```bash
   # Check current rate limit settings in nginx config
   grep -r "limit_req" nginx/
   ```

4. **Static Files Not Found**: Check build process
   ```bash
   docker compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html/
   ```

### Performance Benchmarking

For more detailed performance testing, consider using tools like:

```bash
# Install Apache Bench (if not available)
sudo apt-get install apache2-utils

# Benchmark frontend
ab -n 100 -c 10 http://localhost/

# Benchmark API
ab -n 100 -c 10 http://localhost/api/v1/health

# Benchmark with keep-alive
ab -n 1000 -c 50 -k http://localhost/
```

## Continuous Production Monitoring

Set up ongoing monitoring:

```bash
# Monitor response times
while true; do
  response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/api/v1/health)
  echo "$(date): API response time: ${response_time}s"
  sleep 60
done

# Monitor error rates
while true; do
  status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/health)
  if [ "$status" != "200" ]; then
    echo "$(date): API returned status $status"
  fi
  sleep 30
done
```

This comprehensive production testing approach ensures your production environment is secure, performant, and reliable.