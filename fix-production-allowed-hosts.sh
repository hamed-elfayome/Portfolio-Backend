#!/bin/bash

# Quick fix for ALLOWED_HOSTS issue on production server
echo "🔧 Fixing ALLOWED_HOSTS on production server..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please run ./setup.env.sh prod-docker first"
    exit 1
fi

# Backup current .env file
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update ALLOWED_HOSTS to include localhost
sed -i.bak 's/ALLOWED_HOSTS=api.hamedelfayome.dev,hamedelfayome.dev/ALLOWED_HOSTS=api.hamedelfayome.dev,hamedelfayome.dev,localhost,127.0.0.1/g' .env

echo "✅ ALLOWED_HOSTS updated!"
echo "📋 Current ALLOWED_HOSTS:"
grep "ALLOWED_HOSTS" .env

echo ""
echo "🔄 Restart your Docker containers:"
echo "docker-compose restart web"
echo "# OR"
echo "docker compose restart web"

echo ""
echo "🧪 Test the endpoints:"
echo "curl http://localhost:8000/health/status/"
echo "curl http://localhost:8000/api/v1/status/"
