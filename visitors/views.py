"""
Visitor analytics views for session management and insights.
"""
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import logging

from .models import VisitorSession, PageView, VisitorInteraction
from .analytics_service import SessionAnalyticsService

logger = logging.getLogger(__name__)

class AnalyticsRateThrottle(AnonRateThrottle):
    """Custom rate throttle for analytics endpoints."""
    rate = '100/hour'

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def session_statistics(request):
    """Get comprehensive session statistics."""
    try:
        # Get days parameter (default 30)
        days = int(request.GET.get('days', 30))
        days = min(max(days, 1), 365)  # Limit between 1 and 365 days
        
        analytics_service = SessionAnalyticsService()
        stats = analytics_service.get_session_statistics(days)
        
        return Response({
            'success': True,
            'data': stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting session statistics: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve session statistics',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def visitor_insights(request, session_id):
    """Get detailed insights for a specific visitor session."""
    try:
        analytics_service = SessionAnalyticsService()
        insights = analytics_service.get_visitor_insights(session_id)
        
        if 'error' in insights:
            return Response({
                'success': False,
                'error': insights['error'],
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': insights,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting visitor insights: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve visitor insights',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def real_time_analytics(request):
    """Get real-time analytics for current active sessions."""
    try:
        analytics_service = SessionAnalyticsService()
        analytics = analytics_service.get_real_time_analytics()
        
        if 'error' in analytics:
            return Response({
                'success': False,
                'error': analytics['error'],
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'data': analytics,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real-time analytics: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve real-time analytics',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def engagement_metrics(request):
    """Get engagement metrics for the specified period."""
    try:
        # Get days parameter (default 7)
        days = int(request.GET.get('days', 7))
        days = min(max(days, 1), 90)  # Limit between 1 and 90 days
        
        analytics_service = SessionAnalyticsService()
        metrics = analytics_service.get_engagement_metrics(days)
        
        if 'error' in metrics:
            return Response({
                'success': False,
                'error': metrics['error'],
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'data': metrics,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting engagement metrics: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve engagement metrics',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def current_session_info(request):
    """Get information about the current visitor session."""
    try:
        if not hasattr(request, 'visitor_session') or not request.visitor_session:
            return Response({
                'success': False,
                'error': 'No active visitor session',
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        session = request.visitor_session
        
        # Get recent page views for this session
        recent_page_views = PageView.objects.filter(
            visitor_session=session
        ).order_by('-created_at')[:5]
        
        # Get recent interactions for this session
        recent_interactions = VisitorInteraction.objects.filter(
            visitor_session=session
        ).order_by('-created_at')[:5]
        
        session_info = {
            'session_id': str(session.session_id),
            'session_key': session.session_key,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'session_duration': str(session.get_session_duration()),
            'page_views_count': session.page_views_count,
            'device_type': session.device_type,
            'browser': session.browser,
            'is_bot': session.is_bot,
            'is_recruiter': session.is_recruiter,
            'ip_address': session.ip_address,
            'referrer': session.referrer,
            'recent_page_views': [
                {
                    'page_url': pv.page_url,
                    'page_title': pv.page_title,
                    'time_on_page': str(pv.time_on_page) if pv.time_on_page else None,
                    'created_at': pv.created_at.isoformat()
                }
                for pv in recent_page_views
            ],
            'recent_interactions': [
                {
                    'type': interaction.interaction_type,
                    'details': interaction.details,
                    'created_at': interaction.created_at.isoformat()
                }
                for interaction in recent_interactions
            ]
        }
        
        return Response({
            'success': True,
            'data': session_info,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting current session info: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve current session info',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def popular_pages(request):
    """Get popular pages for the specified period."""
    try:
        # Get days parameter (default 7)
        days = int(request.GET.get('days', 7))
        days = min(max(days, 1), 90)  # Limit between 1 and 90 days
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get top pages
        top_pages = PageView.objects.filter(
            created_at__gte=start_date
        ).values(
            'page_url', 'page_title'
        ).annotate(
            view_count=Count('id'),
            unique_visitors=Count('visitor_session', distinct=True)
        ).order_by('-view_count')[:20]
        
        return Response({
            'success': True,
            'data': {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'top_pages': list(top_pages)
            },
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting popular pages: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve popular pages',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@throttle_classes([AnalyticsRateThrottle])
def visitor_behavior_summary(request):
    """Get visitor behavior summary for the specified period."""
    try:
        # Get days parameter (default 7)
        days = int(request.GET.get('days', 7))
        days = min(max(days, 1), 90)  # Limit between 1 and 90 days
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get behavior statistics
        total_sessions = VisitorSession.objects.filter(created_at__gte=start_date).count()
        bounce_sessions = VisitorSession.objects.filter(
            created_at__gte=start_date,
            page_views_count=1
        ).count()
        engaged_sessions = VisitorSession.objects.filter(
            created_at__gte=start_date,
            page_views_count__gt=1
        ).count()
        
        # Get interaction statistics
        chat_sessions = VisitorSession.objects.filter(
            created_at__gte=start_date,
            interactions__interaction_type__in=['chat_start', 'chat_message']
        ).distinct().count()
        
        job_analysis_sessions = VisitorSession.objects.filter(
            created_at__gte=start_date,
            interactions__interaction_type='job_analysis'
        ).distinct().count()
        
        # Get device and browser distribution
        device_distribution = dict(VisitorSession.objects.filter(
            created_at__gte=start_date
        ).values('device_type').annotate(
            count=Count('id')
        ).values_list('device_type', 'count'))
        
        browser_distribution = dict(VisitorSession.objects.filter(
            created_at__gte=start_date
        ).values('browser').annotate(
            count=Count('id')
        ).values_list('browser', 'count'))
        
        behavior_summary = {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': timezone.now().isoformat(),
            'total_sessions': total_sessions,
            'bounce_sessions': bounce_sessions,
            'engaged_sessions': engaged_sessions,
            'bounce_rate': (bounce_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'engagement_rate': (engaged_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'chat_sessions': chat_sessions,
            'job_analysis_sessions': job_analysis_sessions,
            'chat_rate': (chat_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'job_analysis_rate': (job_analysis_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'device_distribution': device_distribution,
            'browser_distribution': browser_distribution
        }
        
        return Response({
            'success': True,
            'data': behavior_summary,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting visitor behavior summary: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve visitor behavior summary',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)