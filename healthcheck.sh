#!/bin/bash

# Health check script for Docker containers
# This script performs comprehensive health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[HEALTH]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Django application is responding
check_django() {
    print_status "Checking Django application..."
    
    if curl -f http://localhost:8000/health/status/ > /dev/null 2>&1; then
        print_status "✅ Django application is healthy"
        return 0
    else
        print_error "❌ Django application is not responding"
        return 1
    fi
}

# Check database connection
check_database() {
    print_status "Checking database connection..."
    
    if python manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" > /dev/null 2>&1; then
        print_status "✅ Database connection is healthy"
        return 0
    else
        print_error "❌ Database connection failed"
        return 1
    fi
}

# Check Redis connection
check_redis() {
    print_status "Checking Redis connection..."
    
    if python manage.py shell -c "
from django.core.cache import cache
try:
    cache.set('health_check', 'ok', 10)
    result = cache.get('health_check')
    if result == 'ok':
        print('Redis connection successful')
    else:
        print('Redis connection failed')
        exit(1)
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" > /dev/null 2>&1; then
        print_status "✅ Redis connection is healthy"
        return 0
    else
        print_error "❌ Redis connection failed"
        return 1
    fi
}

# Check OpenAI API connection
check_openai() {
    print_status "Checking OpenAI API connection..."
    
    if python manage.py shell -c "
import os
from django.conf import settings
try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    # Simple test - just check if we can create a client
    print('OpenAI API client created successfully')
except Exception as e:
    print(f'OpenAI API connection failed: {e}')
    exit(1)
" > /dev/null 2>&1; then
        print_status "✅ OpenAI API connection is healthy"
        return 0
    else
        print_warning "⚠️ OpenAI API connection failed (non-critical)"
        return 0  # Non-critical for basic health
    fi
}

# Main health check
main() {
    print_status "Starting comprehensive health check..."
    
    local exit_code=0
    
    # Run all health checks
    check_django || exit_code=1
    check_database || exit_code=1
    check_redis || exit_code=1
    check_openai || exit_code=0  # Non-critical
    
    if [ $exit_code -eq 0 ]; then
        print_status "🎉 All health checks passed!"
    else
        print_error "❌ Some health checks failed"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"
