#!/bin/bash

# Deployment Script for AI-Powered Developer Portfolio Site
# This script handles the complete deployment process

set -e  # Exit on any error

echo "🚀 Starting deployment of AI Portfolio Site..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please create one based on .env.example"
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
required_vars=("SECRET_KEY" "DB_NAME" "DB_USER" "DB_PASSWORD" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_status "Environment variables validated"

# Pull latest code
print_status "Pulling latest code..."
git pull origin main

# Build Docker images
print_status "Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing services
print_status "Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

# Start database and Redis first
print_status "Starting database and Redis services..."
docker-compose -f docker-compose.prod.yml up -d db redis

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Run database migrations
print_status "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# Collect static files
print_status "Collecting static files..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
print_status "Creating superuser (if needed)..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start all services
print_status "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."
if curl -f http://localhost/health/status/ > /dev/null 2>&1; then
    print_status "✅ Application is healthy and running!"
else
    print_error "❌ Application health check failed"
    print_status "Checking logs..."
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
fi

# Display service status
print_status "Service status:"
docker-compose -f docker-compose.prod.yml ps

# Display useful information
echo ""
print_status "🎉 Deployment completed successfully!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  Access admin: http://localhost/admin/ (admin/admin123)"
echo "  Health check: http://localhost/health/status/"
echo ""
print_status "🔗 Application is now running at: http://localhost"
