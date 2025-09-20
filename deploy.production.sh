#!/bin/bash

# Production Deployment Script for AI-Powered Developer Portfolio Site
# This script handles the complete production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-portfolio-site"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENVIRONMENT_FILE=".env"
BACKUP_DIR="/backups"
LOG_FILE="/var/log/deployment.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if environment file exists
    if [[ ! -f "$ENVIRONMENT_FILE" ]]; then
        error "Environment file $ENVIRONMENT_FILE not found"
    fi
    
    # Check if Docker Compose file exists
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        error "Docker Compose file $DOCKER_COMPOSE_FILE not found"
    fi
    
    success "Prerequisites check passed"
}

# Validate environment variables
validate_environment() {
    log "Validating environment variables..."
    
    # Required variables
    required_vars=(
        "SECRET_KEY"
        "DB_PASSWORD"
        "OPENAI_API_KEY"
        "ALLOWED_HOSTS"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENVIRONMENT_FILE"; then
            error "Required environment variable $var not found in $ENVIRONMENT_FILE"
        fi
    done
    
    # Check if SECRET_KEY is not the default
    if grep -q "django-insecure-change-this-in-production" "$ENVIRONMENT_FILE"; then
        error "SECRET_KEY must be changed from default value"
    fi
    
    success "Environment validation passed"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    # Create backup directory if it doesn't exist
    sudo mkdir -p "$BACKUP_DIR"
    
    # Backup database if it exists
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps db | grep -q "Up"; then
        log "Backing up database..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dump -U portfolio_user portfolio_db > "$BACKUP_DIR/db_backup_$timestamp.sql"
        success "Database backup created: db_backup_$timestamp.sql"
    fi
    
    # Backup media files if they exist
    if [[ -d "media" ]]; then
        log "Backing up media files..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        tar -czf "$BACKUP_DIR/media_backup_$timestamp.tar.gz" media/
        success "Media backup created: media_backup_$timestamp.tar.gz"
    fi
}

# Pull latest code
pull_code() {
    log "Pulling latest code..."
    
    if [[ -d ".git" ]]; then
        git pull origin main || warning "Git pull failed, continuing with current code"
    else
        warning "Not a git repository, skipping code pull"
    fi
}

# Build and deploy
deploy() {
    log "Starting deployment..."
    
    # Stop existing services
    log "Stopping existing services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down || warning "Failed to stop services"
    
    # Build new images
    log "Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    
    # Start services
    log "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Run migrations
    log "Running database migrations..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py migrate --noinput
    
    # Collect static files
    log "Collecting static files..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput
    
    # Create superuser if it doesn't exist
    log "Checking for superuser..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found, please create one manually')
else:
    print('Superuser exists')
" || warning "Superuser check failed"
    
    success "Deployment completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for services to be fully ready
    sleep 10
    
    # Check if web service is responding
    if curl -f http://localhost/health/status/ > /dev/null 2>&1; then
        success "Health check passed"
    else
        error "Health check failed - service not responding"
    fi
    
    # Check database connectivity
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT 1')
" > /dev/null 2>&1; then
        success "Database connectivity check passed"
    else
        error "Database connectivity check failed"
    fi
    
    # Check Redis connectivity
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py shell -c "
from django.core.cache import cache
cache.set('health_check', 'ok', 10)
result = cache.get('health_check')
assert result == 'ok'
" > /dev/null 2>&1; then
        success "Redis connectivity check passed"
    else
        error "Redis connectivity check failed"
    fi
}

# Cleanup old images
cleanup() {
    log "Cleaning up old Docker images..."
    
    # Remove unused images
    docker image prune -f || warning "Failed to prune images"
    
    # Remove unused volumes (be careful with this)
    # docker volume prune -f || warning "Failed to prune volumes"
    
    success "Cleanup completed"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo "=================="
    
    # Show running containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    echo ""
    echo "Service URLs:"
    echo "- Application: http://localhost"
    echo "- Health Check: http://localhost/health/status/"
    echo "- Admin: http://localhost/admin/"
    echo "- API: http://localhost/api/v1/"
    
    echo ""
    echo "Logs:"
    echo "- Application logs: docker-compose -f $DOCKER_COMPOSE_FILE logs web"
    echo "- Database logs: docker-compose -f $DOCKER_COMPOSE_FILE logs db"
    echo "- Nginx logs: docker-compose -f $DOCKER_COMPOSE_FILE logs nginx"
}

# Main deployment function
main() {
    log "Starting production deployment for $PROJECT_NAME"
    
    check_root
    check_prerequisites
    validate_environment
    create_backup
    pull_code
    deploy
    health_check
    cleanup
    show_status
    
    success "Production deployment completed successfully!"
    log "Deployment log saved to: $LOG_FILE"
}

# Handle script arguments
case "${1:-}" in
    "backup")
        check_prerequisites
        create_backup
        ;;
    "health")
        health_check
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [backup|health|status|cleanup|help]"
        echo ""
        echo "Commands:"
        echo "  backup   - Create backup of database and media files"
        echo "  health   - Run health checks"
        echo "  status   - Show deployment status"
        echo "  cleanup  - Clean up old Docker images"
        echo "  help     - Show this help message"
        echo ""
        echo "Default: Run full deployment"
        ;;
    *)
        main
        ;;
esac
