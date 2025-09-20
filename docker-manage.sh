#!/bin/bash

# Docker Management Script for AI Portfolio Site
# This script provides easy commands for managing Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[DOCKER]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Docker Management Script for AI Portfolio Site"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Start development environment"
    echo "  prod        Start production environment"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs        Show logs for all services"
    echo "  logs-web    Show logs for web service only"
    echo "  shell       Open shell in web container"
    echo "  db-shell    Open PostgreSQL shell"
    echo "  migrate     Run database migrations"
    echo "  collectstatic Collect static files"
    echo "  createsuperuser Create Django superuser"
    echo "  test        Run tests in container"
    echo "  clean       Clean up containers and volumes"
    echo "  status      Show status of all services"
    echo "  health      Run health checks"
    echo "  build       Build Docker images"
    echo "  help        Show this help message"
    echo ""
}

# Function to start development environment
start_dev() {
    print_header "Starting development environment..."
    docker-compose up -d
    print_status "Development environment started"
    print_status "Application available at: http://localhost"
    print_status "Admin interface: http://localhost/admin/"
}

# Function to start production environment
start_prod() {
    print_header "Starting production environment..."
    docker-compose -f docker-compose.prod.yml up -d
    print_status "Production environment started"
    print_status "Application available at: http://localhost"
}

# Function to stop all services
stop_services() {
    print_header "Stopping all services..."
    docker-compose down
    docker-compose -f docker-compose.prod.yml down
    print_status "All services stopped"
}

# Function to restart services
restart_services() {
    print_header "Restarting services..."
    docker-compose restart
    print_status "Services restarted"
}

# Function to show logs
show_logs() {
    print_header "Showing logs for all services..."
    docker-compose logs -f
}

# Function to show web logs only
show_web_logs() {
    print_header "Showing logs for web service..."
    docker-compose logs -f web
}

# Function to open shell in web container
open_shell() {
    print_header "Opening shell in web container..."
    docker-compose exec web bash
}

# Function to open database shell
open_db_shell() {
    print_header "Opening PostgreSQL shell..."
    docker-compose exec db psql -U portfolio_user -d portfolio_db
}

# Function to run migrations
run_migrations() {
    print_header "Running database migrations..."
    docker-compose exec web python manage.py migrate
    print_status "Migrations completed"
}

# Function to collect static files
collect_static() {
    print_header "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
    print_status "Static files collected"
}

# Function to create superuser
create_superuser() {
    print_header "Creating Django superuser..."
    docker-compose exec web python manage.py createsuperuser
}

# Function to run tests
run_tests() {
    print_header "Running tests..."
    docker-compose exec web python manage.py test
}

# Function to clean up
cleanup() {
    print_header "Cleaning up containers and volumes..."
    docker-compose down -v
    docker-compose -f docker-compose.prod.yml down -v
    docker system prune -f
    print_status "Cleanup completed"
}

# Function to show status
show_status() {
    print_header "Service status:"
    docker-compose ps
}

# Function to run health checks
run_health_checks() {
    print_header "Running health checks..."
    ./healthcheck.sh
}

# Function to build images
build_images() {
    print_header "Building Docker images..."
    docker-compose build --no-cache
    print_status "Images built successfully"
}

# Main function
main() {
    case "${1:-help}" in
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        logs-web)
            show_web_logs
            ;;
        shell)
            open_shell
            ;;
        db-shell)
            open_db_shell
            ;;
        migrate)
            run_migrations
            ;;
        collectstatic)
            collect_static
            ;;
        createsuperuser)
            create_superuser
            ;;
        test)
            run_tests
            ;;
        clean)
            cleanup
            ;;
        status)
            show_status
            ;;
        health)
            run_health_checks
            ;;
        build)
            build_images
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
