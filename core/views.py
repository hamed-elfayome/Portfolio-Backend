"""
Core views for health checks and basic functionality.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """Basic health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })

def readiness_check(request):
    """Readiness check including database and cache."""
    checks = {
        'database': False,
        'cache': False,
        'overall': False
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = True
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")

    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception as e:
        logger.error(f"Cache check failed: {str(e)}")

    checks['overall'] = checks['database'] and checks['cache']

    status_code = 200 if checks['overall'] else 503
    return JsonResponse(checks, status=status_code)