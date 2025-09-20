#!/bin/bash

# Docker Deployment Script for AI-Powered Developer Portfolio Site
# Usage: ./deploy.docker.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}

echo "🚀 Starting Docker deployment for $ENVIRONMENT environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.development or .env.production.local"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || docker compose down

# Remove old images (optional)
echo "🧹 Cleaning up old images..."
docker system prune -f

# Build new images
echo "🔨 Building Docker images..."
if [ "$ENVIRONMENT" = "prod" ]; then
    docker-compose -f docker-compose.prod.yml build --no-cache || docker compose -f docker-compose.prod.yml build --no-cache
else
    docker-compose build --no-cache || docker compose build --no-cache
fi

# Start services
echo "🚀 Starting services..."
if [ "$ENVIRONMENT" = "prod" ]; then
    docker-compose -f docker-compose.prod.yml up -d || docker compose -f docker-compose.prod.yml up -d
else
    docker-compose up -d || docker compose up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec web python manage.py migrate || docker compose exec web python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput || docker compose exec web python manage.py collectstatic --noinput

# Check health
echo "🏥 Checking service health..."
docker-compose ps || docker compose ps

echo "✅ Deployment completed successfully!"
echo "🌐 Your API is available at:"
echo "   - Local: http://localhost:8000/api/"
echo "   - Production: https://api.hamedelfayome.dev/api/"

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20 web || docker compose logs --tail=20 web
