# Docker Setup Guide

This guide explains how to deploy the AI-Powered Developer Portfolio Site using Docker.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key
- Domain configured (optional)

### 1. Environment Setup
```bash
# Set up environment for development
./setup.env.sh dev

# Or for production
./setup.env.sh prod
```

### 2. Configure Secrets
Edit the `.env` file and update:
```env
OPENAI_API_KEY=sk-your-actual-openai-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 3. Deploy
```bash
# Deploy for development
./deploy.docker.sh dev

# Or for production
./deploy.docker.sh prod
```

## 🐳 Docker Services

### Development (`docker-compose.yml`)
- **web**: Django application (port 8000)
- **db**: PostgreSQL with pgvector (port 5432)
- **redis**: Redis cache (port 6379)
- **nginx**: Reverse proxy (port 80)

### Production (`docker-compose.prod.yml`)
- Same services as development
- Optimized for production
- SSL support ready
- Health checks enabled

## 🔧 Configuration

### Environment Variables
All configuration is done through the `.env` file:

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=api.hamedelfayome.dev,hamedelfayome.dev

# Database
DB_NAME=portfolio_db
DB_USER=portfolio_user
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
```

### Domain Configuration
- **Frontend**: `hamedelfayome.dev`
- **Backend API**: `api.hamedelfayome.dev`

## 📋 Available Commands

### Setup Commands
```bash
# Generate environment file
./setup.env.sh [dev|prod]

# Deploy application
./deploy.docker.sh [dev|prod]
```

### Docker Commands
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Management Commands
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic

# Shell access
docker-compose exec web python manage.py shell
```

## 🔍 Health Checks

### Check Service Status
```bash
# View all services
docker-compose ps

# Check web service health
curl http://localhost:8000/health/status/

# Check API status
curl http://localhost:8000/api/status/
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs db
docker-compose logs redis
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

#### 2. Database Connection Issues
```bash
# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### 3. Redis Connection Issues
```bash
# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

#### 4. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker permissions
sudo usermod -aG docker $USER
```

### Reset Everything
```bash
# Stop and remove all containers
docker-compose down -v

# Remove all images
docker system prune -a

# Rebuild from scratch
./deploy.docker.sh dev
```

## 🔒 Security

### Production Security Checklist
- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable SSL/HTTPS
- [ ] Set up firewall rules
- [ ] Regular security updates

### Environment Security
- Never commit `.env` files
- Use different secrets for each environment
- Rotate secrets regularly
- Monitor access logs

## 📊 Monitoring

### Health Endpoints
- `/health/status/` - Overall health
- `/health/ready/` - Readiness check
- `/health/live/` - Liveness check
- `/api/metrics/` - Application metrics

### Log Files
- Application logs: `logs/django.log`
- Error logs: `logs/errors.log`
- Security logs: `logs/security.log`

## 🌐 Production Deployment

### Domain Setup
1. Configure DNS:
   - `hamedelfayome.dev` → Frontend server
   - `api.hamedelfayome.dev` → Backend server

2. SSL Certificates:
   - Use Let's Encrypt or your SSL provider
   - Place certificates in `ssl/` directory

3. Nginx Configuration:
   - Update `nginx.prod.conf` with your domain
   - Configure SSL redirects

### Performance Optimization
- Enable Redis caching
- Configure database connection pooling
- Set up CDN for static files
- Monitor resource usage

## 📞 Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Verify configuration: `docker-compose config`
3. Test connectivity: `curl http://localhost:8000/api/status/`
4. Review this documentation

## 🔄 Updates

To update the application:
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
./deploy.docker.sh prod
```
