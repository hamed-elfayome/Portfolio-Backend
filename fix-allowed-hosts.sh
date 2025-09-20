#!/bin/bash

# Quick fix for ALLOWED_HOSTS issue
echo "🔧 Fixing ALLOWED_HOSTS in .env file..."

# Update .env file to include localhost
sed -i.bak 's/ALLOWED_HOSTS=api.hamedelfayome.dev,hamedelfayome.dev/ALLOWED_HOSTS=api.hamedelfayome.dev,hamedelfayome.dev,localhost,127.0.0.1/g' .env

echo "✅ ALLOWED_HOSTS updated!"
echo "📋 Current ALLOWED_HOSTS:"
grep "ALLOWED_HOSTS" .env

echo ""
echo "🔄 Restart your Docker containers:"
echo "docker-compose restart web"
echo "# OR"
echo "docker compose restart web"
