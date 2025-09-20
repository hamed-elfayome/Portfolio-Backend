#!/bin/bash

# Environment Setup Script for AI-Powered Developer Portfolio Site
# Usage: ./setup.env.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}

echo "🔧 Setting up environment for $ENVIRONMENT..."

# Generate secrets if needed
echo "🔐 Generating secure secrets..."

# Generate Django SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
echo "Generated SECRET_KEY: $SECRET_KEY"

# Generate database password
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
echo "Generated DB_PASSWORD: $DB_PASSWORD"

# Create environment file
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "📝 Creating production environment file..."
    cp .env.production.local .env
    
    # Update secrets in .env file
    sed -i.bak "s/your-super-secret-production-key-here/$SECRET_KEY/g" .env
    sed -i.bak "s/your-secure-database-password/$DB_PASSWORD/g" .env
    
    # Update database password in docker-compose files
    sed -i.bak "s/F9wm7L4G6vrVoiHdDU_QLw/$DB_PASSWORD/g" docker-compose.yml
    sed -i.bak "s/F9wm7L4G6vrVoiHdDU_QLw/$DB_PASSWORD/g" docker-compose.prod.yml
    
    echo "✅ Production environment configured!"
    echo "⚠️  Please update the following in .env file:"
    echo "   - OPENAI_API_KEY=your-actual-openai-key"
    echo "   - EMAIL_HOST_USER=your-email@gmail.com"
    echo "   - EMAIL_HOST_PASSWORD=your-email-password"
else
    echo "📝 Creating development environment file..."
    cp .env.development .env
    
    # Update secrets in .env file
    sed -i.bak "s/your-development-secret-key-here/$SECRET_KEY/g" .env
    sed -i.bak "s/password/$DB_PASSWORD/g" .env
    
    echo "✅ Development environment configured!"
    echo "⚠️  Please update the following in .env file:"
    echo "   - OPENAI_API_KEY=your-actual-openai-key"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your actual API keys"
echo "2. Run: ./deploy.docker.sh $ENVIRONMENT"
echo "3. Test your API at http://localhost:8000/api/status/"
