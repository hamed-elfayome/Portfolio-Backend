"""
Monitoring and health check API endpoints.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
import logging

# from .monitoring import system_monitor
# from .logging_service import api_logger
# from .exceptions import PortfolioAPIException

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
@never_cache
def health_check(request):
    """Basic health check endpoint."""
    try:
        return JsonResponse({
            'status': 'healthy',
            'timestamp': api_logger.get_request_context().get('timestamp'),
            'service': 'portfolio-api',
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
@never_cache
def readiness_check(request):
    """Comprehensive readiness check including all system components."""
    try:
        health_status = system_monitor.health_checker.run_all_checks()
        
        # Determine if system is ready
        is_ready = health_status['overall_status'] in ['healthy', 'degraded']
        
        response_data = {
            'status': 'ready' if is_ready else 'not_ready',
            'overall_status': health_status['overall_status'],
            'checks': health_status['checks'],
            'timestamp': health_status['timestamp']
        }
        
        status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JsonResponse(response_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Readiness check error: {str(e)}")
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def system_status(request):
    """Get comprehensive system status including health, alerts, and performance."""
    try:
        system_status_data = system_monitor.get_system_status()
        
        return JsonResponse({
            'success': True,
            'data': system_status_data
        })
        
    except Exception as e:
        logger.error(f"System status error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_detail(request, check_name):
    """Get detailed status of a specific health check."""
    try:
        check_status = system_monitor.health_checker.get_check_status(check_name)
        
        if not check_status:
            return JsonResponse({
                'success': False,
                'error': f'Health check {check_name} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return JsonResponse({
            'success': True,
            'data': check_status
        })
        
    except Exception as e:
        logger.error(f"Health check detail error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def performance_metrics(request):
    """Get performance metrics summary."""
    try:
        metrics_summary = system_monitor.performance_monitor.get_all_metrics_summary()
        
        return JsonResponse({
            'success': True,
            'data': {
                'metrics': metrics_summary,
                'timestamp': api_logger.get_request_context().get('timestamp')
            }
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def active_alerts(request):
    """Get all active alerts."""
    try:
        active_alerts = system_monitor.alert_manager.get_active_alerts()
        
        return JsonResponse({
            'success': True,
            'data': {
                'alerts': active_alerts,
                'count': len(active_alerts),
                'timestamp': api_logger.get_request_context().get('timestamp')
            }
        })
        
    except Exception as e:
        logger.error(f"Active alerts error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resolve_alert(request, alert_id):
    """Resolve an alert."""
    try:
        resolution = request.data.get('resolution', 'Manually resolved')
        
        system_monitor.alert_manager.resolve_alert(alert_id, resolution)
        
        return JsonResponse({
            'success': True,
            'message': f'Alert {alert_id} resolved successfully'
        })
        
    except Exception as e:
        logger.error(f"Resolve alert error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def alert_history(request):
    """Get alert history."""
    try:
        limit = int(request.GET.get('limit', 100))
        alert_history = system_monitor.alert_manager.get_alert_history(limit)
        
        return JsonResponse({
            'success': True,
            'data': {
                'alerts': alert_history,
                'count': len(alert_history),
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Alert history error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def security_events(request):
    """Get recent security events."""
    try:
        limit = int(request.GET.get('limit', 100))
        security_events = api_logger.get_security_events(limit)
        
        return JsonResponse({
            'success': True,
            'data': {
                'events': security_events,
                'count': len(security_events),
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Security events error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def run_monitoring_cycle(request):
    """Manually trigger a monitoring cycle."""
    try:
        system_status_data = system_monitor.run_monitoring_cycle()
        
        return JsonResponse({
            'success': True,
            'message': 'Monitoring cycle completed',
            'data': system_status_data
        })
        
    except Exception as e:
        logger.error(f"Monitoring cycle error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_logs(request):
    """Get recent API logs (for debugging purposes)."""
    try:
        # This would typically be restricted in production
        # For now, return a placeholder response
        return JsonResponse({
            'success': True,
            'message': 'API logs endpoint - implementation depends on log storage backend',
            'data': {
                'note': 'In production, this would connect to a log aggregation service',
                'available_logs': [
                    'api.log',
                    'performance.log',
                    'security.log',
                    'ai.log',
                    'errors.log'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"API logs error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
