#!/bin/bash

# Enhanced Docker deployment script for full-stack application
# Supports both development and production environments with proper error handling

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Define color codes for better output formatting
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/deployment.log"

# Environment files
readonly ENV_LOCAL=".env.local"
readonly ENV_PRODUCTION=".env.production"
readonly ENV_TARGET=".env"

# Docker compose files
readonly COMPOSE_DEV="docker-compose.dev.yml"
readonly COMPOSE_PROD="docker-compose.prod.yml"

# Function to log messages with timestamp
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Function to print colored status messages
print_status() {
    local color="$1"
    local message="$2"
    echo -e "${color}✓${NC} $message"
    log_message "INFO" "$message"
}

# Function to print error messages
print_error() {
    local message="$1"
    echo -e "${RED}✗ Error: $message${NC}" >&2
    log_message "ERROR" "$message"
}

# Function to print warning messages
print_warning() {
    local message="$1"
    echo -e "${YELLOW}⚠ Warning: $message${NC}"
    log_message "WARNING" "$message"
}

# Function to print info messages
print_info() {
    local message="$1"
    echo -e "${BLUE}ℹ Info: $message${NC}"
    log_message "INFO" "$message"
}

# Function to show usage information
show_usage() {
    cat << EOF
${CYAN}Docker Deployment Script${NC}

${YELLOW}USAGE:${NC}
    $SCRIPT_NAME <environment> <command> [options]

${YELLOW}ENVIRONMENTS:${NC}
    dev     - Development environment with hot reloading
    prod    - Production environment with nginx reverse proxy

${YELLOW}COMMANDS:${NC}
    up      - Start services
    down    - Stop services
    restart - Restart services
    logs    - Show service logs
    status  - Show service status
    clean   - Clean up containers and images

${YELLOW}OPTIONS:${NC}
    delete  - Remove containers, images, and volumes (use with down/clean)
    -f      - Force operation without confirmation
    -v      - Verbose output
    -h      - Show this help message

${YELLOW}EXAMPLES:${NC}
    $SCRIPT_NAME dev up              # Start development environment
    $SCRIPT_NAME prod up             # Start production environment
    $SCRIPT_NAME dev down delete     # Stop dev and remove everything
    $SCRIPT_NAME prod logs           # Show production logs
    $SCRIPT_NAME dev status          # Check development status
    $SCRIPT_NAME prod clean -f       # Force clean production environment

${YELLOW}PREREQUISITES:${NC}
    - Docker Engine (version 20.10+)
    - Docker Compose (version 2.0+)
    - Environment files (.env.local, .env.production)
    - Docker compose files (docker-compose.dev.yml, docker-compose.prod.yml)

EOF
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker version
check_docker_version() {
    local min_version="20.10"
    local docker_version
    
    if ! docker_version=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1); then
        print_error "Failed to get Docker version"
        return 1
    fi
    
    if ! printf '%s\n%s\n' "$min_version" "$docker_version" | sort -V -C; then
        print_error "Docker version $docker_version is too old. Minimum required: $min_version"
        return 1
    fi
    
    print_status "$GREEN" "Docker version $docker_version detected"
    return 0
}

# Function to check Docker Compose version
check_compose_version() {
    local min_version="2.0"
    local compose_version
    
    # Try docker compose (new) first, then docker-compose (legacy)
    if compose_version=$(docker compose version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1); then
        COMPOSE_CMD="docker compose"
    elif compose_version=$(docker-compose --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1); then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose not found. Please install Docker Compose v2.0+"
        return 1
    fi
    
    if ! printf '%s\n%s\n' "$min_version" "$compose_version" | sort -V -C; then
        print_warning "Docker Compose version $compose_version detected. Recommended: $min_version+"
    else
        print_status "$GREEN" "Docker Compose version $compose_version detected"
    fi
    
    return 0
}

# Function to validate prerequisites
validate_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker Engine first."
        print_info "Visit: https://docs.docker.com/engine/install/"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker service."
        return 1
    fi
    
    # Check Docker version
    if ! check_docker_version; then
        return 1
    fi
    
    # Check Docker Compose
    if ! check_compose_version; then
        return 1
    fi
    
    print_status "$GREEN" "All prerequisites validated successfully"
    return 0
}

# Parse command line arguments
parse_arguments() {
    ENVIRONMENT=""
    COMMAND=""
    FORCE=false
    VERBOSE=false
    DELETE_FLAG=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            dev|prod)
                if [[ -z "$ENVIRONMENT" ]]; then
                    ENVIRONMENT="$1"
                else
                    print_error "Multiple environments specified"
                    return 1
                fi
                ;;
            up|down|restart|logs|status|clean)
                if [[ -z "$COMMAND" ]]; then
                    COMMAND="$1"
                else
                    print_error "Multiple commands specified"
                    return 1
                fi
                ;;
            delete)
                DELETE_FLAG=true
                ;;
            -f|--force)
                FORCE=true
                ;;
            -v|--verbose)
                VERBOSE=true
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown argument: $1"
                show_usage
                return 1
                ;;
        esac
        shift
    done
    
    # Validate required arguments
    if [[ -z "$ENVIRONMENT" ]]; then
        print_error "Environment not specified (dev|prod)"
        show_usage
        return 1
    fi
    
    if [[ -z "$COMMAND" ]]; then
        print_error "Command not specified (up|down|restart|logs|status|clean)"
        show_usage
        return 1
    fi
    
    return 0
}

# Function to detect system information
detect_system_info() {
    local os_name=$(uname -s)
    local os_version=""
    
    case "$os_name" in
        Linux)
            if [[ -f /etc/os-release ]]; then
                os_version=$(grep '^PRETTY_NAME=' /etc/os-release | cut -d'"' -f2)
            fi
            print_status "$GREEN" "System OS: $os_name ($os_version)"
            
            # Get IP address for Linux systems
            if command_exists hostname; then
                local ip_address=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "Unable to detect")
                print_info "Primary IP Address: $ip_address"
            fi
            ;;
        Darwin)
            os_version=$(sw_vers -productVersion 2>/dev/null || echo "Unknown")
            print_status "$GREEN" "System OS: macOS $os_version"
            ;;
        *)
            print_status "$GREEN" "System OS: $os_name"
            ;;
    esac
}

# Function to validate environment files
validate_environment_files() {
    local env_file=""
    
    case "$ENVIRONMENT" in
        dev)
            env_file="$ENV_LOCAL"
            ;;
        prod)
            env_file="$ENV_PRODUCTION"
            ;;
    esac
    
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file '$env_file' not found"
        print_info "Please create the environment file with required configuration"
        return 1
    fi
    
    # Check if environment file is readable
    if [[ ! -r "$env_file" ]]; then
        print_error "Environment file '$env_file' is not readable"
        print_info "Please check file permissions: chmod 644 $env_file"
        return 1
    fi
    
    # Validate required environment variables
    local required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_SERVER" "REDIS_URL" "SECRET_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables in $env_file:"
        for var in "${missing_vars[@]}"; do
            echo -e "  ${RED}✗${NC} $var"
        done
        return 1
    fi
    
    print_status "$GREEN" "Environment file '$env_file' validated successfully"
    return 0
}

# Function to copy environment file with proper error handling
copy_environment_file() {
    local source_file=""
    local backup_file="${ENV_TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
    
    case "$ENVIRONMENT" in
        dev)
            source_file="$ENV_LOCAL"
            ;;
        prod)
            source_file="$ENV_PRODUCTION"
            ;;
    esac
    
    print_info "Preparing environment configuration for $ENVIRONMENT..."
    
    # Backup existing .env file if it exists
    if [[ -f "$ENV_TARGET" ]]; then
        if cp "$ENV_TARGET" "$backup_file" 2>/dev/null; then
            print_info "Existing .env backed up as $backup_file"
        else
            print_warning "Failed to backup existing .env file"
        fi
    fi
    
    # Copy the appropriate environment file
    if cp "$source_file" "$ENV_TARGET" 2>/dev/null; then
        print_status "$GREEN" "Environment file copied: $source_file → $ENV_TARGET"
    else
        print_error "Failed to copy environment file: $source_file → $ENV_TARGET"
        return 1
    fi
    
    # Set proper permissions
    if chmod 644 "$ENV_TARGET" 2>/dev/null; then
        print_status "$GREEN" "Environment file permissions set (644)"
    else
        print_warning "Failed to set environment file permissions"
    fi
    
    return 0
}

# Function to set executable permissions for scripts
set_script_permissions() {
    local scripts=("backend/entrypoint.dev.sh" "backend/entrypoint.prod.sh" "backend/wait-for-it.sh" "backend/run_migrations.sh")
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            if chmod +x "$script" 2>/dev/null; then
                print_status "$GREEN" "Set executable permission: $script"
            else
                print_warning "Failed to set executable permission: $script"
            fi
        fi
    done
}

# Function to validate Docker Compose file
validate_compose_file() {
    local compose_file="$1"
    
    if [[ ! -f "$compose_file" ]]; then
        print_error "Docker Compose file '$compose_file' not found"
        return 1
    fi
    
    if [[ ! -r "$compose_file" ]]; then
        print_error "Docker Compose file '$compose_file' is not readable"
        return 1
    fi
    
    # Validate compose file syntax
    if ! $COMPOSE_CMD -f "$compose_file" config >/dev/null 2>&1; then
        print_error "Docker Compose file '$compose_file' has syntax errors"
        print_info "Run: $COMPOSE_CMD -f $compose_file config"
        return 1
    fi
    
    print_status "$GREEN" "Docker Compose file '$compose_file' validated successfully"
    return 0
}

# Function to create Docker network and volumes with error handling
create_network_and_volumes() {
    print_info "Setting up Docker network and volumes..."
    
    # Create network
    if docker network inspect webnet >/dev/null 2>&1; then
        print_info "Docker network 'webnet' already exists"
    else
        if docker network create webnet >/dev/null 2>&1; then
            print_status "$GREEN" "Docker network 'webnet' created successfully"
        else
            print_error "Failed to create Docker network 'webnet'"
            return 1
        fi
    fi
    
    # Create volumes
    local volumes=("users-db-data" "redis-data")
    
    for volume in "${volumes[@]}"; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            print_info "Docker volume '$volume' already exists"
        else
            if docker volume create "$volume" >/dev/null 2>&1; then
                print_status "$GREEN" "Docker volume '$volume' created successfully"
            else
                print_error "Failed to create Docker volume '$volume'"
                return 1
            fi
        fi
    done
    
    return 0
}

# Function to get compose file based on environment
get_compose_file() {
    case "$ENVIRONMENT" in
        dev)
            echo "$COMPOSE_DEV"
            ;;
        prod)
            echo "$COMPOSE_PROD"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            return 1
            ;;
    esac
}

# Function to start containers
start_containers() {
    local compose_file
    compose_file=$(get_compose_file) || return 1
    
    print_info "Starting $ENVIRONMENT environment..."
    
    # Create network and volumes
    if ! create_network_and_volumes; then
        return 1
    fi
    
    # Build containers
    print_info "Building Docker images..."
    if $COMPOSE_CMD -f "$compose_file" build; then
        print_status "$GREEN" "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        return 1
    fi
    
    # Start containers
    print_info "Starting Docker containers..."
    if $COMPOSE_CMD -f "$compose_file" up -d; then
        print_status "$GREEN" "Docker containers started successfully"
        
        # Show running containers
        print_info "Running containers:"
        $COMPOSE_CMD -f "$compose_file" ps
        
        # Show access information
        show_access_info
    else
        print_error "Failed to start Docker containers"
        return 1
    fi
    
    return 0
}

# Function to stop containers
stop_containers() {
    local compose_file
    compose_file=$(get_compose_file) || return 1
    
    print_info "Stopping $ENVIRONMENT environment..."
    
    if $COMPOSE_CMD -f "$compose_file" down; then
        print_status "$GREEN" "Docker containers stopped successfully"
    else
        print_error "Failed to stop Docker containers"
        return 1
    fi
    
    return 0
}

# Function to restart containers
restart_containers() {
    print_info "Restarting $ENVIRONMENT environment..."
    
    if stop_containers && start_containers; then
        print_status "$GREEN" "Environment restarted successfully"
    else
        print_error "Failed to restart environment"
        return 1
    fi
    
    return 0
}

# Function to show container logs
show_logs() {
    local compose_file
    compose_file=$(get_compose_file) || return 1
    
    print_info "Showing logs for $ENVIRONMENT environment..."
    $COMPOSE_CMD -f "$compose_file" logs -f
}

# Function to show container status
show_status() {
    local compose_file
    compose_file=$(get_compose_file) || return 1
    
    print_info "Status for $ENVIRONMENT environment:"
    $COMPOSE_CMD -f "$compose_file" ps
    
    # Show resource usage if possible
    if command_exists docker; then
        echo
        print_info "Resource usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null || true
    fi
}

# Function to clean up containers and resources
clean_environment() {
    local compose_file
    compose_file=$(get_compose_file) || return 1
    
    local cleanup_args="--remove-orphans"
    
    if [[ "$DELETE_FLAG" == true ]]; then
        if [[ "$FORCE" == false ]]; then
            echo -e "${YELLOW}⚠ This will remove containers, images, and volumes. Are you sure? (y/N)${NC}"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                print_info "Cleanup cancelled"
                return 0
            fi
        fi
        cleanup_args="$cleanup_args --rmi all --volumes"
        print_info "Performing full cleanup (containers, images, volumes)..."
    else
        print_info "Performing basic cleanup (containers only)..."
    fi
    
    if $COMPOSE_CMD -f "$compose_file" down $cleanup_args; then
        print_status "$GREEN" "Cleanup completed successfully"
    else
        print_error "Cleanup failed"
        return 1
    fi
    
    return 0
}

# Function to show access information after startup
show_access_info() {
    echo
    print_info "Access Information:"
    
    case "$ENVIRONMENT" in
        dev)
            echo -e "  ${CYAN}Frontend:${NC} http://localhost:5173"
            echo -e "  ${CYAN}Backend API:${NC} http://localhost:8000"
            echo -e "  ${CYAN}API Docs:${NC} http://localhost:8000/docs"
            echo -e "  ${CYAN}Flower (Celery):${NC} http://localhost:5555"
            ;;
        prod)
            echo -e "  ${CYAN}Application:${NC} https://banwee.com (or your configured domain)"
            echo -e "  ${CYAN}API:${NC} https://banwee.com/api/v1/"
            echo -e "  ${CYAN}Flower (Celery):${NC} http://localhost:5555"
            ;;
    esac
    
    echo
    print_info "Useful commands:"
    echo -e "  ${CYAN}View logs:${NC} $SCRIPT_NAME $ENVIRONMENT logs"
    echo -e "  ${CYAN}Check status:${NC} $SCRIPT_NAME $ENVIRONMENT status"
    echo -e "  ${CYAN}Stop services:${NC} $SCRIPT_NAME $ENVIRONMENT down"
}

# Main execution function
main() {
    # Initialize log file
    echo "=== Docker Deployment Script Started at $(date) ===" >> "$LOG_FILE"
    
    # Parse command line arguments
    if ! parse_arguments "$@"; then
        exit 1
    fi
    
    # Show script header
    echo -e "${CYAN}=== Docker Deployment Script ===${NC}"
    echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
    echo -e "${BLUE}Command: $COMMAND${NC}"
    echo -e "${BLUE}Timestamp: $(date)${NC}"
    echo
    
    # Detect system information
    detect_system_info
    
    # Validate prerequisites
    if ! validate_prerequisites; then
        exit 1
    fi
    
    # Validate environment files
    if ! validate_environment_files; then
        exit 1
    fi
    
    # Get and validate compose file
    local compose_file
    compose_file=$(get_compose_file) || exit 1
    
    if ! validate_compose_file "$compose_file"; then
        exit 1
    fi
    
    # Copy environment file and set permissions
    if ! copy_environment_file; then
        exit 1
    fi
    
    # Set script permissions
    set_script_permissions
    
    # Execute the requested command
    case "$COMMAND" in
        up)
            if ! start_containers; then
                print_error "Failed to start $ENVIRONMENT environment"
                exit 1
            fi
            ;;
        down)
            if [[ "$DELETE_FLAG" == true ]]; then
                if ! clean_environment; then
                    print_error "Failed to clean $ENVIRONMENT environment"
                    exit 1
                fi
            else
                if ! stop_containers; then
                    print_error "Failed to stop $ENVIRONMENT environment"
                    exit 1
                fi
            fi
            ;;
        restart)
            if ! restart_containers; then
                print_error "Failed to restart $ENVIRONMENT environment"
                exit 1
            fi
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            if ! clean_environment; then
                print_error "Failed to clean $ENVIRONMENT environment"
                exit 1
            fi
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
    
    print_status "$GREEN" "Operation completed successfully"
    log_message "INFO" "Script completed successfully"
}

# Error handling
trap 'print_error "Script interrupted"; exit 130' INT
trap 'print_error "Script terminated"; exit 143' TERM

# Run main function with all arguments
main "$@"
