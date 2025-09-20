"""
Production monitoring and health checks for AI-Powered Developer Portfolio Site.
"""

import logging
import time
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import psutil
import redis
from openai import OpenAI

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health check system for production monitoring."""
    
    def __init__(self):
        self.checks = {}
        self.overall_status = 'healthy'
        self.start_time = time.time()
    
    def check_database(self):
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            self.checks['database'] = {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'connection_pool': connection.connection_pool.size,
                'checked_at': timezone.now().isoformat()
            }
            
            if response_time > 1000:  # More than 1 second
                self.checks['database']['status'] = 'degraded'
                self.overall_status = 'degraded'
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            self.checks['database'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': timezone.now().isoformat()
            }
            self.overall_status = 'unhealthy'
    
    def check_redis(self):
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test basic operations
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            cache.delete('health_check')
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if result == 'ok':
                self.checks['redis'] = {
                    'status': 'healthy',
                    'response_time_ms': round(response_time, 2),
                    'checked_at': timezone.now().isoformat()
                }
            else:
                self.checks['redis'] = {
                    'status': 'unhealthy',
                    'error': 'Cache operation failed',
                    'checked_at': timezone.now().isoformat()
                }
                self.overall_status = 'unhealthy'
                
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            self.checks['redis'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': timezone.now().isoformat()
            }
            self.overall_status = 'unhealthy'
    
    def check_openai(self):
        """Check OpenAI API connectivity."""
        try:
            if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
                self.checks['openai'] = {
                    'status': 'not_configured',
                    'message': 'OpenAI API key not configured',
                    'checked_at': timezone.now().isoformat()
                }
                return
            
            start_time = time.time()
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Test with a simple request
            response = client.models.list()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            self.checks['openai'] = {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'models_available': len(response.data) if response.data else 0,
                'checked_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")
            self.checks['openai'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': timezone.now().isoformat()
            }
            if self.overall_status == 'healthy':
                self.overall_status = 'degraded'
    
    def check_system_resources(self):
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.checks['system'] = {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'checked_at': timezone.now().isoformat()
            }
            
            # Check for resource warnings
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                self.checks['system']['status'] = 'warning'
                if self.overall_status == 'healthy':
                    self.overall_status = 'degraded'
                    
        except Exception as e:
            logger.error(f"System resources check failed: {str(e)}")
            self.checks['system'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': timezone.now().isoformat()
            }
    
    def check_application_health(self):
        """Check application-specific health metrics."""
        try:
            from core.models import Profile
            from projects.models import Project
            from ai_services.models import DocumentChunk
            
            # Check data integrity
            profile_count = Profile.objects.filter(is_active=True).count()
            project_count = Project.objects.count()
            chunk_count = DocumentChunk.objects.count()
            
            self.checks['application'] = {
                'status': 'healthy',
                'active_profiles': profile_count,
                'total_projects': project_count,
                'document_chunks': chunk_count,
                'checked_at': timezone.now().isoformat()
            }
            
            # Check for data issues
            if profile_count == 0:
                self.checks['application']['status'] = 'warning'
                self.checks['application']['warning'] = 'No active profiles found'
                if self.overall_status == 'healthy':
                    self.overall_status = 'degraded'
                    
        except Exception as e:
            logger.error(f"Application health check failed: {str(e)}")
            self.checks['application'] = {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': timezone.now().isoformat()
            }
    
    def run_all_checks(self):
        """Run all health checks."""
        self.check_database()
        self.check_redis()
        self.check_openai()
        self.check_system_resources()
        self.check_application_health()
        
        total_time = (time.time() - self.start_time) * 1000
        
        return {
            'status': self.overall_status,
            'checks': self.checks,
            'total_check_time_ms': round(total_time, 2),
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': getattr(settings, 'ENVIRONMENT', 'production')
        }


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Basic health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'AI Portfolio Site',
        'version': getattr(settings, 'VERSION', '1.0.0')
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """Comprehensive readiness check for production deployment."""
    checker = HealthChecker()
    result = checker.run_all_checks()
    
    # Determine HTTP status code
    if result['status'] == 'healthy':
        status_code = status.HTTP_200_OK
    elif result['status'] == 'degraded':
        status_code = status.HTTP_200_OK  # Still operational
    else:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(result, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """Kubernetes liveness probe endpoint."""
    return JsonResponse({
        'status': 'alive',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    """Application metrics for monitoring."""
    try:
        from core.models import Profile
        from projects.models import Project
        from visitors.models import VisitorSession
        from ai_chat.models import Conversation, Message
        from job_matching.models import JobAnalysis
        
        # Get basic metrics
        metrics_data = {
            'timestamp': timezone.now().isoformat(),
            'application': {
                'profiles': Profile.objects.filter(is_active=True).count(),
                'projects': Project.objects.count(),
                'visitor_sessions': VisitorSession.objects.count(),
                'conversations': Conversation.objects.count(),
                'messages': Message.objects.count(),
                'job_analyses': JobAnalysis.objects.count(),
            },
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
            }
        }
        
        # Add cache metrics if available
        try:
            cache_info = cache._cache.get_client().info()
            metrics_data['cache'] = {
                'connected_clients': cache_info.get('connected_clients', 0),
                'used_memory': cache_info.get('used_memory', 0),
                'keyspace_hits': cache_info.get('keyspace_hits', 0),
                'keyspace_misses': cache_info.get('keyspace_misses', 0),
            }
        except:
            metrics_data['cache'] = {'status': 'unavailable'}
        
        return Response(metrics_data)
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return Response({
            'error': 'Metrics collection failed',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerformanceMonitor:
    """Performance monitoring utilities."""
    
    @staticmethod
    def log_slow_query(query, duration):
        """Log slow database queries."""
        if duration > 1.0:  # Log queries taking more than 1 second
            logger.warning(f"Slow query detected: {duration:.2f}s - {query}")
    
    @staticmethod
    def log_api_performance(endpoint, method, duration, status_code):
        """Log API endpoint performance."""
        if duration > 2.0:  # Log API calls taking more than 2 seconds
            logger.warning(f"Slow API call: {method} {endpoint} - {duration:.2f}s - {status_code}")
    
    @staticmethod
    def log_ai_performance(operation, duration, tokens_used=None):
        """Log AI service performance."""
        logger.info(f"AI operation: {operation} - {duration:.2f}s" + 
                   (f" - {tokens_used} tokens" if tokens_used else ""))


# Middleware for performance monitoring
class PerformanceMonitoringMiddleware:
    """Middleware to monitor request performance."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 2.0:
            logger.warning(f"Slow request: {request.method} {request.path} - {duration:.2f}s")
        
        # Add performance headers
        response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response