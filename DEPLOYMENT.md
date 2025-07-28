# Deployment Guide

This guide provides comprehensive instructions for deploying the full-stack application in both development and production environments using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)
- [Common Issues](#common-issues)
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