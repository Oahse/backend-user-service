# Deployment Guide

This guide provides comprehensive instructions for deploying the full-stack application in both development and production environments using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Environment Configuration](#environment-configuration)
- [Testing and Validation](#testing-and-validation)
- [Deployment Script Usage](#deployment-script-usage)
- [Troubleshooting](#troubleshooting)
- [Common Issues](#common-issues)
- [Environment-Specific Examples](#environment-specific-examples)
- [Maintenance](#maintenance)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Docker**: Version 20.10+ with Docker Compose V2
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Storage**: Minimum 10GB free space
- **Network**: Internet connection for pulling Docker images

### Required Software

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose V2
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### File Permissions

Ensure the deployment script is executable:

```bash
chmod +x run_docker.sh
```

## Quick Start

### Development Environment

```bash
# Start development environment
./run_docker.sh dev up

# Access services
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
# Flower (Celery Monitor): http://localhost:5555
```

### Production Environment

```bash
# Start production environment
./run_docker.sh prod up

# Access services
# Application: http://localhost (or your domain)
# API: http://localhost/api/v1/
# Flower: http://localhost/flower/
```

## Development Environment

### Starting Development Environment

The development environment is optimized for rapid development with hot reloading and direct service access.

```bash
# Start all services
./run_docker.sh dev up

# Start in detached mode
./run_docker.sh dev up -d

# View logs
./run_docker.sh dev logs

# Stop services
./run_docker.sh dev down
```

### Development Features

- **Hot Reloading**: Frontend and backend automatically reload on code changes
- **Direct Access**: Services accessible on their native ports
- **Debug Mode**: Detailed logging and error messages
- **Volume Mounts**: Source code mounted for real-time development

### Development Service Ports

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Frontend | 5173 | http://localhost:5173 | Vite dev server |
| Backend | 8000 | http://localhost:8000 | FastAPI with reload |
| PostgreSQL | 5432 | localhost:5432 | Database (internal) |
| Redis | 6379 | localhost:6379 | Cache/Broker (internal) |
| Flower | 5555 | http://localhost:5555 | Celery monitoring |

### Development Workflow

1. **Code Changes**: Edit files in `frontend/` or `backend/` directories
2. **Automatic Reload**: Services automatically detect and reload changes
3. **Testing**: Use direct port access for API testing and debugging
4. **Database**: Access PostgreSQL directly for database operations
5. **Monitoring**: Use Flower to monitor background tasks

## Production Environment

### Starting Production Environment

The production environment uses nginx as a reverse proxy with optimized builds and security configurations.

```bash
# Start production environment
./run_docker.sh prod up

# Start in detached mode (recommended)
./run_docker.sh prod up -d

# View logs
./run_docker.sh prod logs

# Stop services
./run_docker.sh prod down
```

### Production Features

- **nginx Reverse Proxy**: All traffic routed through nginx
- **Static File Serving**: Optimized frontend asset delivery
- **SSL/TLS Support**: HTTPS with certificate management
- **Security Headers**: Comprehensive security header implementation
- **Rate Limiting**: API protection against abuse
- **Optimized Builds**: Minified and compressed assets

### Production Service Architecture

```
Internet → nginx:80/443 → Frontend (Static Files)
                       → Backend API (/api/v1/)
                       → Flower (/flower/)
```

### SSL/HTTPS Configuration

For production HTTPS, place your SSL certificates in the nginx/ssl/prod/ directory:

```bash
# Certificate files
nginx/ssl/prod/fullchain.pem    # SSL certificate chain
nginx/ssl/prod/privkey.pem      # Private key

# Let's Encrypt example
certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/prod/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/prod/
```

## Testing and Validation

### Development Environment Testing

Before deploying to production, thoroughly test the development environment to ensure all components work correctly.

#### Automated Testing Script

The project includes automated testing scripts for both environments:

```bash
# Test development environment
./test_dev_environment.sh

# Test production environment  
./test_prod_environment.sh
```

#### Manual Development Testing Steps

1. **Start Development Environment**
   ```bash
   ./run_docker.sh dev up
   ```

2. **Verify Service Accessibility**
   ```bash
   # Test frontend
   curl -f http://localhost:5173 || echo "Frontend not accessible"
   
   # Test backend API
   curl -f http://localhost:8000/api/v1/health || echo "Backend API not accessible"
   
   # Test API documentation
   curl -f http://localhost:8000/docs || echo "API docs not accessible"
   
   # Test Celery monitoring
   curl -f http://localhost:5555 || echo "Flower not accessible"
   ```

3. **Test Hot Reloading**
   ```bash
   # Make a change to frontend code
   echo "console.log('Test change');" >> frontend/src/App.jsx
   
   # Make a change to backend code
   echo "# Test comment" >> backend/main.py
   
   # Verify changes are reflected without restart
   ```

4. **Test Database Connectivity**
   ```bash
   # Connect to database
   docker compose -f docker-compose.dev.yml exec users-db psql -U postgres -d app -c "\dt"
   
   # Test backend database connection
   docker compose -f docker-compose.dev.yml exec userservice python -c "from core.database import engine; print('DB Connected:', engine.url)"
   ```

5. **Test Redis Connectivity**
   ```bash
   # Test Redis connection
   docker compose -f docker-compose.dev.yml exec redis redis-cli ping
   
   # Test backend Redis connection
   docker compose -f docker-compose.dev.yml exec userservice python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print('Redis Connected:', r.ping())"
   ```

### Production Environment Testing

Production testing ensures the nginx reverse proxy, SSL configuration, and optimized builds work correctly.

#### Manual Production Testing Steps

1. **Start Production Environment**
   ```bash
   ./run_docker.sh prod up
   ```

2. **Test nginx Reverse Proxy**
   ```bash
   # Test frontend serving through nginx
   curl -f http://localhost/ || echo "Frontend not accessible through nginx"
   
   # Test API routing through nginx
   curl -f http://localhost/api/v1/health || echo "API not accessible through nginx"
   
   # Test static file serving
   curl -f http://localhost/assets/ || echo "Static assets not accessible"
   ```

3. **Test SSL Configuration (if configured)**
   ```bash
   # Test HTTPS redirect
   curl -I http://localhost/ | grep -i location
   
   # Test SSL certificate
   openssl s_client -connect localhost:443 -servername yourdomain.com < /dev/null
   ```

4. **Test Security Headers**
   ```bash
   # Check security headers
   curl -I http://localhost/ | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)"
   ```

5. **Test Rate Limiting**
   ```bash
   # Test API rate limiting (adjust based on your limits)
   for i in {1..100}; do curl -s http://localhost/api/v1/health; done
   ```

6. **Performance Testing**
   ```bash
   # Test frontend load time
   time curl -s http://localhost/ > /dev/null
   
   # Test API response time
   time curl -s http://localhost/api/v1/health > /dev/null
   ```

### Validation Checklist

#### Development Environment Validation
- [ ] All services start successfully
- [ ] Frontend accessible on port 5173
- [ ] Backend API accessible on port 8000
- [ ] API documentation accessible
- [ ] Hot reloading works for frontend
- [ ] Hot reloading works for backend
- [ ] Database connections work
- [ ] Redis connections work
- [ ] Celery worker processes tasks
- [ ] Flower monitoring accessible

#### Production Environment Validation
- [ ] All services start successfully
- [ ] nginx serves frontend correctly
- [ ] nginx proxies API requests correctly
- [ ] Static files served with proper caching
- [ ] SSL/HTTPS works (if configured)
- [ ] Security headers present
- [ ] Rate limiting functional
- [ ] Database connections work
- [ ] Redis connections work
- [ ] Celery worker processes tasks
- [ ] Performance meets requirements

## Deployment Script Usage

The `run_docker.sh` script is the primary tool for managing the application lifecycle. It provides comprehensive error handling, validation, and status reporting.

### Script Features

- **Environment Validation**: Checks Docker installation and versions
- **Prerequisite Checking**: Validates required files and configurations
- **Error Handling**: Comprehensive error reporting with colored output
- **Logging**: All operations logged to `deployment.log`
- **Status Reporting**: Clear status messages and progress indicators

### Basic Usage

```bash
# General syntax
./run_docker.sh <environment> <command> [options]

# Environment options
dev     # Development environment
prod    # Production environment

# Command options
up      # Start services
down    # Stop services
restart # Restart services
logs    # Show service logs
status  # Show service status
clean   # Clean up containers and images
```

### Advanced Usage Examples

```bash
# Start development with verbose output
./run_docker.sh dev up -v

# Stop production and remove all containers/images/volumes
./run_docker.sh prod down delete -f

# Check status of development environment
./run_docker.sh dev status

# View logs for production environment
./run_docker.sh prod logs

# Clean up development environment without confirmation
./run_docker.sh dev clean -f

# Restart production environment
./run_docker.sh prod restart
```

### Script Validation Process

The script performs the following validations before executing commands:

1. **System Prerequisites**
   - Docker Engine version (minimum 20.10)
   - Docker Compose version (minimum 2.0)
   - Docker daemon running status

2. **File Validation**
   - Environment files exist and are readable
   - Docker Compose files exist and have valid syntax
   - Required environment variables present

3. **Permission Checks**
   - Script executable permissions
   - Environment file permissions
   - Backend script permissions

4. **Network and Volume Setup**
   - Docker network creation
   - Volume creation and validation

### Error Handling

The script provides detailed error messages and suggestions:

```bash
# Example error output
✗ Error: Environment file '.env.local' not found
ℹ Info: Please create the environment file with required configuration

✗ Error: Docker version 19.03 is too old. Minimum required: 20.10
ℹ Info: Visit: https://docs.docker.com/engine/install/

✗ Error: Missing required environment variables in .env.local:
  ✗ POSTGRES_PASSWORD
  ✗ SECRET_KEY
```

## Environment Configuration

### Environment Files

The application uses environment-specific configuration files:

- `.env.local` - Development environment variables
- `.env.production` - Production environment variables

### Development Configuration Example

```bash
# .env.local
ENVIRONMENT=development
DEBUG=true

# Database Configuration
POSTGRES_SERVER=users-db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethis
POSTGRES_DB=app

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Backend Configuration
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (optional for dev)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Frontend Configuration
VITE_API_URL=http://localhost:8000
```

### Production Configuration Example

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false

# Database Configuration
POSTGRES_SERVER=users-db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=app

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Backend Configuration
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Frontend Configuration
VITE_API_URL=https://yourdomain.com/api/v1

# SSL Configuration
SSL_CERT_PATH=/etc/nginx/ssl/fullchain.pem
SSL_KEY_PATH=/etc/nginx/ssl/privkey.pem
```

### Security Considerations

- **Secrets**: Use strong, unique passwords and secret keys
- **CORS**: Configure appropriate CORS origins for your domain
- **SSL**: Always use HTTPS in production
- **Database**: Use secure database passwords
- **Environment Variables**: Never commit sensitive data to version control

## Troubleshooting

### General Troubleshooting Steps

1. **Check Service Status**
   ```bash
   docker compose ps
   docker compose logs [service-name]
   ```

2. **Verify Environment Files**
   ```bash
   # Check if environment file exists and is readable
   ls -la .env.local .env.production
   cat .env.local  # Verify content (be careful with secrets)
   ```

3. **Check Docker Resources**
   ```bash
   docker system df  # Check disk usage
   docker system prune  # Clean up unused resources
   ```

4. **Network Connectivity**
   ```bash
   # Test service connectivity
   docker compose exec backend ping users-db
   docker compose exec backend ping redis
   ```

### Service-Specific Troubleshooting

#### Frontend Issues

**Problem**: Frontend not loading or showing blank page
```bash
# Check frontend logs
docker compose logs frontend

# Verify build process
docker compose exec frontend npm run build

# Check nginx configuration (production)
docker compose exec nginx nginx -t
```

**Problem**: Hot reloading not working in development
```bash
# Verify volume mounts
docker compose exec frontend ls -la /app

# Check file permissions
sudo chown -R $USER:$USER frontend/
```

#### Backend Issues

**Problem**: Backend API not responding
```bash
# Check backend logs
docker compose logs userservice

# Verify database connection
docker compose exec userservice python -c "from core.database import engine; print(engine.url)"

# Test API directly
curl http://localhost:8000/api/v1/health
```

**Problem**: Database connection errors
```bash
# Check database status
docker compose exec users-db pg_isready

# Verify database credentials
docker compose exec users-db psql -U postgres -d app -c "\dt"
```

#### nginx Issues

**Problem**: nginx failing to start
```bash
# Test nginx configuration
docker compose exec nginx nginx -t

# Check nginx logs
docker compose logs nginx

# Verify SSL certificates (production)
docker compose exec nginx ls -la /etc/nginx/ssl/
```

**Problem**: SSL certificate issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/prod/fullchain.pem -text -noout

# Verify certificate chain
openssl verify -CAfile nginx/ssl/prod/fullchain.pem nginx/ssl/prod/fullchain.pem
```

## Common Issues

### Issue 1: Port Already in Use

**Symptoms**: Error binding to port 5173, 8000, or 80/443

**Solution**:
```bash
# Find process using the port
sudo lsof -i :5173
sudo lsof -i :8000
sudo lsof -i :80

# Kill the process or change port in docker-compose
sudo kill -9 <PID>

# Or stop conflicting services
sudo systemctl stop apache2  # If Apache is running on port 80
sudo systemctl stop nginx    # If system nginx is running
```

### Issue 2: Permission Denied Errors

**Symptoms**: Permission denied when accessing files or running containers

**Solution**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x run_docker.sh

# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker  # Or logout and login again
```

### Issue 3: Database Connection Refused

**Symptoms**: Backend cannot connect to PostgreSQL

**Solution**:
```bash
# Check if database container is running
docker compose ps users-db

# Wait for database to be ready
docker compose exec users-db pg_isready -U postgres

# Check database logs
docker compose logs users-db

# Verify environment variables
docker compose exec userservice env | grep POSTGRES
```

### Issue 4: Frontend Build Failures

**Symptoms**: Frontend container fails to build or serve files

**Solution**:
```bash
# Clear npm cache
docker compose exec frontend npm cache clean --force

# Rebuild frontend container
docker compose build --no-cache frontend

# Check Node.js version compatibility
docker compose exec frontend node --version
docker compose exec frontend npm --version
```

### Issue 5: SSL Certificate Problems

**Symptoms**: HTTPS not working or certificate errors

**Solution**:
```bash
# Verify certificate files exist
ls -la nginx/ssl/prod/

# Check certificate format
file nginx/ssl/prod/fullchain.pem
file nginx/ssl/prod/privkey.pem

# Test certificate validity
openssl x509 -in nginx/ssl/prod/fullchain.pem -text -noout | grep "Not After"

# Restart nginx after certificate update
docker compose restart nginx
```

### Issue 6: High Memory Usage

**Symptoms**: System running out of memory or containers being killed

**Solution**:
```bash
# Check container resource usage
docker stats

# Limit container memory (add to docker-compose.yml)
services:
  frontend:
    mem_limit: 512m
  userservice:
    mem_limit: 1g

# Clean up unused Docker resources
docker system prune -a
docker volume prune
```

### Issue 7: Deployment Script Failures

**Symptoms**: run_docker.sh script fails with validation errors

**Solution**:
```bash
# Check script permissions
chmod +x run_docker.sh

# Verify Docker installation
docker --version
docker compose version

# Check environment file exists
ls -la .env.local .env.production

# Validate Docker Compose syntax
docker compose -f docker-compose.dev.yml config
docker compose -f docker-compose.prod.yml config

# Check deployment logs
tail -f deployment.log
```

### Issue 8: Environment Variable Issues

**Symptoms**: Services fail to start due to missing or incorrect environment variables

**Solution**:
```bash
# Validate environment file content
grep -E "^[A-Z_]+=.+" .env.local | wc -l  # Should show number of variables

# Check for missing required variables
required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "SECRET_KEY" "REDIS_URL")
for var in "${required_vars[@]}"; do
    grep -q "^${var}=" .env.local || echo "Missing: $var"
done

# Verify environment file is copied correctly
ls -la .env
cat .env | head -5  # Check first few lines

# Test environment variable loading
docker compose -f docker-compose.dev.yml exec userservice env | grep POSTGRES
```

### Issue 9: Service Health Check Failures

**Symptoms**: Services fail health checks and don't start properly

**Solution**:
```bash
# Check service health status
docker compose ps

# View health check logs
docker compose logs users-db | grep health
docker compose logs redis | grep health

# Manually test health checks
docker compose exec users-db pg_isready -U postgres
docker compose exec redis redis-cli ping

# Increase health check timeout (in docker-compose.yml)
healthcheck:
  test: ["CMD", "pg_isready", "-U", "postgres"]
  interval: 10s
  timeout: 10s
  retries: 5
  start_period: 30s
```

### Issue 10: Testing Script Failures

**Symptoms**: Automated testing scripts fail or return false positives

**Solution**:
```bash
# Run tests with verbose output
bash -x ./test_dev_environment.sh

# Check individual test components
curl -v http://localhost:5173
curl -v http://localhost:8000/api/v1/health

# Verify service readiness before testing
docker compose ps | grep -E "(healthy|Up)"

# Wait for services to be fully ready
sleep 30 && ./test_dev_environment.sh

# Check test script permissions
chmod +x test_dev_environment.sh test_prod_environment.sh
```

## Environment-Specific Examples

### Development Environment Complete Setup

This section provides complete, working examples for setting up the development environment from scratch.

#### Development Environment File (.env.local)

```bash
# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database Configuration
POSTGRES_SERVER=users-db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=devpassword123
POSTGRES_DB=app
DATABASE_URL=postgresql://postgres:devpassword123@users-db:5432/app

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Backend Configuration
SECRET_KEY=dev-secret-key-change-in-production-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173"]

# Email Configuration (optional for development)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-dev-email@gmail.com
SMTP_PASSWORD=your-app-password

# Frontend Configuration
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=Development App

# Development-specific settings
PYTHONPATH=/usr/src/app
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

#### Development Docker Compose Configuration

Key aspects of the development setup:

```yaml
# docker-compose.dev.yml (key sections)
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000

  userservice:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/usr/src/app
    depends_on:
      users-db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

#### Development Testing Commands

```bash
# Complete development environment test
./run_docker.sh dev up

# Wait for services to be ready
sleep 30

# Test all endpoints
echo "Testing frontend..."
curl -f http://localhost:5173 && echo "✓ Frontend OK" || echo "✗ Frontend Failed"

echo "Testing backend API..."
curl -f http://localhost:8000/api/v1/health && echo "✓ Backend OK" || echo "✗ Backend Failed"

echo "Testing API documentation..."
curl -f http://localhost:8000/docs && echo "✓ API Docs OK" || echo "✗ API Docs Failed"

echo "Testing Celery monitoring..."
curl -f http://localhost:5555 && echo "✓ Flower OK" || echo "✗ Flower Failed"

# Test database connectivity
docker compose -f docker-compose.dev.yml exec userservice python -c "
from core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✓ Database connection OK')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
"

# Test Redis connectivity
docker compose -f docker-compose.dev.yml exec userservice python -c "
import redis
try:
    r = redis.from_url('redis://redis:6379/0')
    r.ping()
    print('✓ Redis connection OK')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
"
```

### Production Environment Complete Setup

#### Production Environment File (.env.production)

```bash
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Database Configuration
POSTGRES_SERVER=users-db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-production-password-123!
POSTGRES_DB=app
DATABASE_URL=postgresql://postgres:secure-production-password-123!@users-db:5432/app

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Backend Configuration
SECRET_KEY=super-secure-production-secret-key-change-this-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Email Configuration
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=your-production-app-password

# Frontend Configuration
VITE_API_URL=https://yourdomain.com/api/v1
VITE_APP_TITLE=Production App

# SSL Configuration
SSL_CERT_PATH=/etc/nginx/ssl/fullchain.pem
SSL_KEY_PATH=/etc/nginx/ssl/privkey.pem

# Security Settings
SECURE_COOKIES=true
HTTPS_ONLY=true

# Production-specific settings
PYTHONPATH=/usr/src/app
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

#### Production nginx Configuration

```nginx
# nginx/conf.d/prod.conf (example)
upstream backend {
    server userservice:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend static files
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/v1/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # Flower monitoring (restrict access in production)
    location /flower/ {
        proxy_pass http://flower:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Basic auth for production
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

#### Production Testing Commands

```bash
# Complete production environment test
./run_docker.sh prod up

# Wait for services to be ready
sleep 60

# Test nginx reverse proxy
echo "Testing frontend through nginx..."
curl -f http://localhost/ && echo "✓ Frontend through nginx OK" || echo "✗ Frontend through nginx Failed"

echo "Testing API through nginx..."
curl -f http://localhost/api/v1/health && echo "✓ API through nginx OK" || echo "✗ API through nginx Failed"

# Test SSL (if configured)
echo "Testing HTTPS redirect..."
curl -I http://localhost/ | grep -q "301\|302" && echo "✓ HTTPS redirect OK" || echo "✗ HTTPS redirect Failed"

# Test security headers
echo "Testing security headers..."
curl -I http://localhost/ | grep -q "X-Frame-Options" && echo "✓ Security headers OK" || echo "✗ Security headers Failed"

# Test static file caching
echo "Testing static file caching..."
curl -I http://localhost/assets/index.js | grep -q "Cache-Control" && echo "✓ Static caching OK" || echo "✗ Static caching Failed"

# Performance test
echo "Testing response times..."
time curl -s http://localhost/ > /dev/null && echo "✓ Frontend response time acceptable"
time curl -s http://localhost/api/v1/health > /dev/null && echo "✓ API response time acceptable"
```

### Environment Switching

#### Switching from Development to Production

```bash
# Stop development environment
./run_docker.sh dev down

# Clean up development resources (optional)
./run_docker.sh dev clean delete -f

# Start production environment
./run_docker.sh prod up

# Verify production is running
./run_docker.sh prod status
```

#### Switching from Production to Development

```bash
# Stop production environment
./run_docker.sh prod down

# Start development environment
./run_docker.sh dev up

# Verify development is running
./run_docker.sh dev status
```

### Database Migration Between Environments

```bash
# Export data from development
docker compose -f docker-compose.dev.yml exec users-db pg_dump -U postgres app > dev_backup.sql

# Import data to production (be careful!)
docker compose -f docker-compose.prod.yml exec -T users-db psql -U postgres app < dev_backup.sql
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor application logs for errors
- Check disk space usage
- Verify all services are running

#### Weekly
- Update Docker images
- Review security logs
- Backup database

#### Monthly
- Update SSL certificates (if not automated)
- Review and rotate secrets
- Performance optimization review

### Backup Procedures

#### Database Backup
```bash
# Create database backup
docker compose exec users-db pg_dump -U postgres app > backup_$(date +%Y%m%d).sql

# Restore database backup
docker compose exec -T users-db psql -U postgres app < backup_20240101.sql
```

#### Configuration Backup
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env.local .env.production \
  docker-compose.dev.yml docker-compose.prod.yml \
  nginx/
```

### Updates and Upgrades

#### Updating Application Code
```bash
# Pull latest code
git pull origin main

# Rebuild and restart services
./run_docker.sh dev down
./run_docker.sh dev up --build
```

#### Updating Docker Images
```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

### Monitoring and Logging

#### Log Management
```bash
# View logs for all services
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View logs for specific service
docker compose logs userservice

# Limit log output
docker compose logs --tail=100 userservice
```

#### Health Monitoring
```bash
# Check service health
docker compose ps

# Monitor resource usage
docker stats

# Check application health endpoints
curl http://localhost:8000/api/v1/health
```

### Performance Optimization

#### Production Optimizations
- Enable gzip compression in nginx
- Configure proper caching headers
- Optimize database queries
- Use connection pooling
- Monitor and tune container resources

#### Development Optimizations
- Use Docker layer caching
- Optimize volume mounts
- Configure appropriate resource limits
- Use multi-stage builds for faster rebuilds

---

For additional support or questions, please refer to the project documentation or contact the development team.