# Development Environment Testing

This document describes the comprehensive testing system for the development environment, implementing task 7 from the Docker app restructure specification.

## Overview

The development environment testing system validates:
- ✅ Development environment startup
- ✅ Hot reloading functionality for frontend and backend
- ✅ Service communication and API connectivity
- ✅ Database and Redis connections
- ✅ Container health and resource usage
- ✅ Environment variable configuration

## Test Scripts

### 1. `test_dev_environment.sh` - Main Test Script

Comprehensive testing script that validates all aspects of the development environment.

**Usage:**
```bash
# Make executable (if not already)
chmod +x test_dev_environment.sh

# Run full test suite
./test_dev_environment.sh
```

**Test Categories:**

1. **Prerequisites Check**
   - Docker installation and daemon status
   - Docker Compose availability
   - Required tools (curl, netcat)
   - Environment and compose file existence

2. **Environment Startup**
   - Development environment startup via `run_docker.sh dev up`
   - Container status verification
   - Service initialization

3. **Service Health Checks**
   - PostgreSQL TCP connectivity (port 5432)
   - Redis TCP connectivity (port 6379)
   - Backend health endpoint (`/health`)
   - Frontend accessibility (port 5173)
   - Flower monitoring (port 5555)

4. **API Connectivity**
   - Backend root endpoint response
   - API documentation accessibility (`/docs`)
   - CORS header validation

5. **Database Connectivity**
   - Backend-to-database connection via health check
   - Direct database connection test

6. **Redis Connectivity**
   - Backend-to-Redis connection via health check
   - Direct Redis ping test

7. **Hot Reloading Functionality**
   - Backend uvicorn `--reload` flag verification
   - Frontend Vite dev server detection
   - Volume mount validation for code changes

8. **Service Communication**
   - Backend-to-database communication test
   - Backend-to-Redis communication test
   - Celery-to-Redis broker connection test

9. **Container Resource Usage**
   - CPU usage monitoring (alerts if >80%)
   - Memory usage monitoring (alerts if >80%)

10. **Environment Variables**
    - Backend required environment variables
    - Frontend API URL configuration

### 2. `validate_dev_test_structure.sh` - Structure Validation

Validates the test implementation structure without requiring Docker to be running.

**Usage:**
```bash
# Make executable (if not already)
chmod +x validate_dev_test_structure.sh

# Run validation
./validate_dev_test_structure.sh
```

**Validation Areas:**
- Test script structure and functions
- Required files existence
- Docker Compose configuration
- Environment configuration
- Backend and frontend setup
- Test coverage completeness

## Test Requirements Coverage

The testing system addresses the following requirements from the specification:

- **Requirement 8.1**: Development environment testing ✅
- **Requirement 8.3**: Service communication and API connectivity ✅
- **Requirement 8.4**: Database and Redis connections ✅
- **Requirement 8.5**: Hot reloading functionality ✅

## Expected Test Results

### Successful Test Run Output:
```
=== Development Environment Testing ===
Testing comprehensive development environment functionality

=== Prerequisites Check ===
✓ PASS Docker availability
✓ PASS Docker Compose availability
✓ PASS curl availability
✓ PASS netcat availability
✓ PASS Environment file exists
✓ PASS Docker Compose file exists

=== Environment Startup ===
✓ PASS Development environment startup
✓ PASS All containers running

=== Service Health Checks ===
✓ PASS PostgreSQL connectivity
✓ PASS Redis connectivity
✓ PASS Backend health check
✓ PASS Frontend accessibility
✓ PASS Flower accessibility

=== API Connectivity ===
✓ PASS Backend root endpoint
✓ PASS API documentation
✓ PASS CORS configuration

=== Database Connectivity ===
✓ PASS Backend-Database connection
✓ PASS Direct database connection

=== Redis Connectivity ===
✓ PASS Backend-Redis connection
✓ PASS Direct Redis connection

=== Hot Reloading Functionality ===
✓ PASS Backend hot reloading
✓ PASS Frontend hot reloading
✓ PASS Backend volume mount
✓ PASS Frontend volume mount

=== Service Communication ===
✓ PASS Backend-Database communication
✓ PASS Backend-Redis communication
✓ PASS Celery-Redis communication

=== Container Resource Usage ===
✓ PASS CPU usage check
✓ PASS Memory usage check

=== Environment Variables ===
✓ PASS Backend environment variables
✓ PASS Frontend environment variables

=== Test Summary ===
Total Tests: 26
Passed: 26
Failed: 0
All tests passed! ✓
```

## Service Endpoints Tested

| Service | Endpoint | Port | Test Type |
|---------|----------|------|-----------|
| Frontend | http://localhost:5173 | 5173 | HTTP accessibility |
| Backend API | http://localhost:8000 | 8000 | HTTP + health check |
| API Docs | http://localhost:8000/docs | 8000 | HTTP accessibility |
| Flower | http://localhost:5555 | 5555 | HTTP accessibility |
| PostgreSQL | localhost:5432 | 5432 | TCP + pg_isready |
| Redis | localhost:6379 | 6379 | TCP + ping |

## Hot Reloading Verification

The tests verify hot reloading by checking:

1. **Backend Hot Reloading:**
   - uvicorn process running with `--reload` flag
   - Volume mount: `./backend:/usr/src/app`
   - Exclusion of `__pycache__` from volume mount

2. **Frontend Hot Reloading:**
   - Vite dev server process running
   - Volume mount: `./frontend:/app`
   - Exclusion of `node_modules` from volume mount

## Troubleshooting

### Common Issues:

1. **Docker not running:**
   ```
   ✗ FAIL Docker availability
   → Docker not found or not running
   ```
   **Solution:** Start Docker daemon

2. **Port conflicts:**
   ```
   ✗ FAIL Frontend accessibility
   → Frontend not accessible
   ```
   **Solution:** Check if ports 5173, 8000, 5555, 5432, 6379 are available

3. **Environment file issues:**
   ```
   ✗ FAIL Environment file exists
   → .env.local not found
   ```
   **Solution:** Ensure `.env.local` exists with required variables

4. **Service startup timeout:**
   ```
   ✗ FAIL Backend health check
   → Backend health endpoint not accessible
   ```
   **Solution:** Wait longer for services to initialize, check logs with `./run_docker.sh dev logs`

### Debug Commands:

```bash
# Check container status
docker compose -f docker-compose.dev.yml ps

# View service logs
./run_docker.sh dev logs

# Check specific service logs
docker compose -f docker-compose.dev.yml logs userservice
docker compose -f docker-compose.dev.yml logs frontend

# Test individual endpoints
curl http://localhost:8000/health
curl http://localhost:5173
curl http://localhost:5555

# Check database connection
docker exec users-db pg_isready -U postgres -d users_db

# Check Redis connection
docker exec redis redis-cli ping
```

## Log Files

- **Test Results:** `dev_test_results.log` - Detailed test execution log
- **Deployment Log:** `deployment.log` - Docker deployment script log

## Integration with Specification

This testing system implements task 7 from `.kiro/specs/docker-app-restructure/tasks.md`:

```markdown
- [-] 7. Test development environment
  - Create comprehensive testing for development environment startup
  - Verify hot reloading functionality for frontend and backend
  - Test service communication and API connectivity
  - Validate database and Redis connections
  - _Requirements: 8.1, 8.3, 8.4, 8.5_
```

The implementation provides:
- ✅ Comprehensive testing for development environment startup
- ✅ Hot reloading functionality verification
- ✅ Service communication and API connectivity tests
- ✅ Database and Redis connection validation
- ✅ Full coverage of requirements 8.1, 8.3, 8.4, and 8.5

## Next Steps

After successful development environment testing:
1. Proceed to task 8: Test production environment
2. Create deployment documentation (task 9)
3. Validate all environments work correctly

## Usage Examples

### Quick Test Run:
```bash
./test_dev_environment.sh
```

### Validate Structure Only:
```bash
./validate_dev_test_structure.sh
```

### Start Environment and Test:
```bash
./run_docker.sh dev up
./test_dev_environment.sh
./run_docker.sh dev down
```

This comprehensive testing system ensures the development environment is properly configured, all services communicate correctly, and hot reloading functionality works as expected for efficient development workflows.