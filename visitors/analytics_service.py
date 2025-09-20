"""
Session analytics service for visitor behavior insights and reporting.
"""
from django.db.models import Count, Avg, Q, F, Sum, Min, Max
from django.utils import timezone
from datetime import timedelta, datetime
from typing import Dict, List, Any, Optional
import logging

from .models import VisitorSession, PageView, VisitorInteraction

logger = logging.getLogger(__name__)

class SessionAnalyticsService:
    """Service for analyzing visitor sessions and providing insights."""
    
    def __init__(self):
        self.logger = logger

    def get_session_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive session statistics for the specified period."""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Basic session counts
            total_sessions = VisitorSession.objects.filter(created_at__gte=start_date).count()
            unique_visitors = VisitorSession.objects.filter(created_at__gte=start_date).values('ip_address').distinct().count()
            bot_sessions = VisitorSession.objects.filter(created_at__gte=start_date, is_bot=True).count()
            recruiter_sessions = VisitorSession.objects.filter(created_at__gte=start_date, is_recruiter=True).count()
            
            # Device and browser distribution
            device_distribution = self._get_device_distribution(start_date)
            browser_distribution = self._get_browser_distribution(start_date)
            
            # Session duration statistics
            duration_stats = self._get_session_duration_stats(start_date)
            
            # Page view statistics
            page_view_stats = self._get_page_view_stats(start_date)
            
            # Interaction statistics
            interaction_stats = self._get_interaction_stats(start_date)
            
            # Geographic distribution (if available)
            geographic_stats = self._get_geographic_stats(start_date)
            
            return {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'total_sessions': total_sessions,
                'unique_visitors': unique_visitors,
                'bot_sessions': bot_sessions,
                'recruiter_sessions': recruiter_sessions,
                'human_sessions': total_sessions - bot_sessions,
                'device_distribution': device_distribution,
                'browser_distribution': browser_distribution,
                'duration_stats': duration_stats,
                'page_view_stats': page_view_stats,
                'interaction_stats': interaction_stats,
                'geographic_stats': geographic_stats,
                'conversion_rate': self._calculate_conversion_rate(start_date),
                'engagement_score': self._calculate_engagement_score(start_date)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session statistics: {str(e)}")
            return {}

    def get_visitor_insights(self, session_id: str) -> Dict[str, Any]:
        """Get detailed insights for a specific visitor session."""
        try:
            session = VisitorSession.objects.get(session_id=session_id)
            
            # Get page views for this session
            page_views = PageView.objects.filter(visitor_session=session).order_by('created_at')
            
            # Get interactions for this session
            interactions = VisitorInteraction.objects.filter(visitor_session=session).order_by('created_at')
            
            # Calculate session metrics
            session_duration = session.get_session_duration()
            total_page_views = page_views.count()
            avg_time_per_page = self._calculate_avg_time_per_page(page_views)
            
            # Analyze behavior patterns
            behavior_analysis = self._analyze_visitor_behavior(session, page_views, interactions)
            
            # Get popular pages
            popular_pages = self._get_popular_pages_for_session(page_views)
            
            # Get interaction summary
            interaction_summary = self._get_interaction_summary(interactions)
            
            return {
                'session_id': str(session.session_id),
                'session_key': session.session_key,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'session_duration': str(session_duration),
                'total_page_views': total_page_views,
                'avg_time_per_page': str(avg_time_per_page) if avg_time_per_page else None,
                'device_type': session.device_type,
                'browser': session.browser,
                'is_bot': session.is_bot,
                'is_recruiter': session.is_recruiter,
                'ip_address': session.ip_address,
                'referrer': session.referrer,
                'page_views': [
                    {
                        'page_url': pv.page_url,
                        'page_title': pv.page_title,
                        'time_on_page': str(pv.time_on_page) if pv.time_on_page else None,
                        'created_at': pv.created_at.isoformat()
                    }
                    for pv in page_views
                ],
                'interactions': [
                    {
                        'type': interaction.interaction_type,
                        'details': interaction.details,
                        'created_at': interaction.created_at.isoformat()
                    }
                    for interaction in interactions
                ],
                'behavior_analysis': behavior_analysis,
                'popular_pages': popular_pages,
                'interaction_summary': interaction_summary,
                'engagement_score': self._calculate_session_engagement_score(session, page_views, interactions)
            }
            
        except VisitorSession.DoesNotExist:
            return {'error': 'Session not found'}
        except Exception as e:
            self.logger.error(f"Error getting visitor insights: {str(e)}")
            return {'error': str(e)}

    def get_real_time_analytics(self) -> Dict[str, Any]:
        """Get real-time analytics for current active sessions."""
        try:
            # Active sessions (last 30 minutes)
            active_threshold = timezone.now() - timedelta(minutes=30)
            active_sessions = VisitorSession.objects.filter(last_activity__gte=active_threshold)
            
            # Current online visitors
            online_visitors = active_sessions.filter(is_bot=False).count()
            
            # Recent page views (last 10 minutes)
            recent_threshold = timezone.now() - timedelta(minutes=10)
            recent_page_views = PageView.objects.filter(created_at__gte=recent_threshold)
            
            # Recent interactions (last 10 minutes)
            recent_interactions = VisitorInteraction.objects.filter(created_at__gte=recent_threshold)
            
            # Top pages being viewed right now
            current_popular_pages = recent_page_views.values('page_url', 'page_title').annotate(
                view_count=Count('id')
            ).order_by('-view_count')[:5]
            
            # Current interaction types
            current_interaction_types = recent_interactions.values('interaction_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return {
                'timestamp': timezone.now().isoformat(),
                'online_visitors': online_visitors,
                'active_sessions': active_sessions.count(),
                'recent_page_views': recent_page_views.count(),
                'recent_interactions': recent_interactions.count(),
                'current_popular_pages': list(current_popular_pages),
                'current_interaction_types': list(current_interaction_types),
                'device_distribution': self._get_device_distribution(active_threshold),
                'browser_distribution': self._get_browser_distribution(active_threshold)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time analytics: {str(e)}")
            return {'error': str(e)}

    def get_engagement_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get engagement metrics for the specified period."""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Sessions with multiple page views
            engaged_sessions = VisitorSession.objects.filter(
                created_at__gte=start_date,
                page_views_count__gt=1
            ).count()
            
            # Sessions with interactions
            interactive_sessions = VisitorSession.objects.filter(
                created_at__gte=start_date,
                interactions__isnull=False
            ).distinct().count()
            
            # Sessions with chat interactions
            chat_sessions = VisitorSession.objects.filter(
                created_at__gte=start_date,
                interactions__interaction_type__in=['chat_start', 'chat_message']
            ).distinct().count()
            
            # Sessions with job analysis
            job_analysis_sessions = VisitorSession.objects.filter(
                created_at__gte=start_date,
                interactions__interaction_type='job_analysis'
            ).distinct().count()
            
            # Average session duration
            avg_duration = VisitorSession.objects.filter(
                created_at__gte=start_date,
                time_spent__isnull=False
            ).aggregate(avg_duration=Avg('time_spent'))['avg_duration']
            
            # Bounce rate (sessions with only 1 page view)
            total_sessions = VisitorSession.objects.filter(created_at__gte=start_date).count()
            bounce_rate = ((total_sessions - engaged_sessions) / total_sessions * 100) if total_sessions > 0 else 0
            
            return {
                'period_days': days,
                'total_sessions': total_sessions,
                'engaged_sessions': engaged_sessions,
                'interactive_sessions': interactive_sessions,
                'chat_sessions': chat_sessions,
                'job_analysis_sessions': job_analysis_sessions,
                'engagement_rate': (engaged_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'interaction_rate': (interactive_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'chat_rate': (chat_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'job_analysis_rate': (job_analysis_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'bounce_rate': bounce_rate,
                'avg_session_duration': str(avg_duration) if avg_duration else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting engagement metrics: {str(e)}")
            return {'error': str(e)}

    def _get_device_distribution(self, start_date: datetime) -> Dict[str, int]:
        """Get device type distribution for the period."""
        return dict(VisitorSession.objects.filter(
            created_at__gte=start_date
        ).values('device_type').annotate(
            count=Count('id')
        ).values_list('device_type', 'count'))

    def _get_browser_distribution(self, start_date: datetime) -> Dict[str, int]:
        """Get browser distribution for the period."""
        return dict(VisitorSession.objects.filter(
            created_at__gte=start_date
        ).values('browser').annotate(
            count=Count('id')
        ).values_list('browser', 'count'))

    def _get_session_duration_stats(self, start_date: datetime) -> Dict[str, Any]:
        """Get session duration statistics."""
        sessions_with_duration = VisitorSession.objects.filter(
            created_at__gte=start_date,
            time_spent__isnull=False
        )
        
        if not sessions_with_duration.exists():
            return {}
        
        stats = sessions_with_duration.aggregate(
            avg_duration=Avg('time_spent'),
            min_duration=Min('time_spent'),
            max_duration=Max('time_spent')
        )
        
        return {
            'avg_duration': str(stats['avg_duration']) if stats['avg_duration'] else None,
            'min_duration': str(stats['min_duration']) if stats['min_duration'] else None,
            'max_duration': str(stats['max_duration']) if stats['max_duration'] else None,
            'sessions_with_duration': sessions_with_duration.count()
        }

    def _get_page_view_stats(self, start_date: datetime) -> Dict[str, Any]:
        """Get page view statistics."""
        total_page_views = PageView.objects.filter(created_at__gte=start_date).count()
        
        # Top pages
        top_pages = PageView.objects.filter(created_at__gte=start_date).values(
            'page_url', 'page_title'
        ).annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:10]
        
        return {
            'total_page_views': total_page_views,
            'top_pages': list(top_pages)
        }

    def _get_interaction_stats(self, start_date: datetime) -> Dict[str, Any]:
        """Get interaction statistics."""
        total_interactions = VisitorInteraction.objects.filter(created_at__gte=start_date).count()
        
        # Interaction type distribution
        interaction_types = VisitorInteraction.objects.filter(
            created_at__gte=start_date
        ).values('interaction_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_interactions': total_interactions,
            'interaction_types': list(interaction_types)
        }

    def _get_geographic_stats(self, start_date: datetime) -> Dict[str, Any]:
        """Get geographic distribution (if available)."""
        # This would require IP geolocation service
        # For now, return empty dict
        return {}

    def _calculate_conversion_rate(self, start_date: datetime) -> float:
        """Calculate conversion rate (sessions with job analysis or contact)."""
        total_sessions = VisitorSession.objects.filter(created_at__gte=start_date).count()
        converted_sessions = VisitorSession.objects.filter(
            created_at__gte=start_date,
            interactions__interaction_type__in=['job_analysis', 'contact']
        ).distinct().count()
        
        return (converted_sessions / total_sessions * 100) if total_sessions > 0 else 0

    def _calculate_engagement_score(self, start_date: datetime) -> float:
        """Calculate overall engagement score."""
        sessions = VisitorSession.objects.filter(created_at__gte=start_date)
        
        if not sessions.exists():
            return 0
        
        # Weighted engagement factors
        avg_page_views = sessions.aggregate(avg=Avg('page_views_count'))['avg'] or 0
        interactive_sessions = sessions.filter(interactions__isnull=False).distinct().count()
        total_sessions = sessions.count()
        
        # Simple engagement score (0-100)
        page_view_score = min(avg_page_views * 10, 50)  # Max 50 points for page views
        interaction_score = (interactive_sessions / total_sessions) * 50  # Max 50 points for interactions
        
        return round(page_view_score + interaction_score, 2)

    def _calculate_avg_time_per_page(self, page_views) -> Optional[timedelta]:
        """Calculate average time per page for a session."""
        page_views_with_time = page_views.filter(time_on_page__isnull=False)
        
        if not page_views_with_time.exists():
            return None
        
        total_time = sum((pv.time_on_page for pv in page_views_with_time), timedelta())
        return total_time / page_views_with_time.count()

    def _analyze_visitor_behavior(self, session, page_views, interactions) -> Dict[str, Any]:
        """Analyze visitor behavior patterns."""
        behavior = {
            'session_type': 'bounce' if page_views.count() <= 1 else 'engaged',
            'interaction_level': 'none',
            'primary_interest': 'unknown',
            'conversion_likelihood': 'low'
        }
        
        # Determine interaction level
        if interactions.filter(interaction_type__in=['chat_start', 'chat_message']).exists():
            behavior['interaction_level'] = 'high'
        elif interactions.filter(interaction_type='job_analysis').exists():
            behavior['interaction_level'] = 'medium'
        elif interactions.exists():
            behavior['interaction_level'] = 'low'
        
        # Determine primary interest
        if interactions.filter(interaction_type='job_analysis').exists():
            behavior['primary_interest'] = 'job_opportunities'
        elif interactions.filter(interaction_type__in=['chat_start', 'chat_message']).exists():
            behavior['primary_interest'] = 'general_inquiry'
        elif page_views.filter(page_url__contains='/projects/').exists():
            behavior['primary_interest'] = 'projects'
        
        # Determine conversion likelihood
        if behavior['interaction_level'] == 'high' and behavior['primary_interest'] == 'job_opportunities':
            behavior['conversion_likelihood'] = 'high'
        elif behavior['interaction_level'] in ['medium', 'high']:
            behavior['conversion_likelihood'] = 'medium'
        
        return behavior

    def _get_popular_pages_for_session(self, page_views) -> List[Dict[str, Any]]:
        """Get popular pages for a specific session."""
        page_counts = {}
        for pv in page_views:
            key = pv.page_url
            if key in page_counts:
                page_counts[key]['count'] += 1
            else:
                page_counts[key] = {
                    'page_url': pv.page_url,
                    'page_title': pv.page_title,
                    'count': 1
                }
        
        return sorted(page_counts.values(), key=lambda x: x['count'], reverse=True)

    def _get_interaction_summary(self, interactions) -> Dict[str, int]:
        """Get summary of interactions for a session."""
        summary = {}
        for interaction in interactions:
            interaction_type = interaction.interaction_type
            summary[interaction_type] = summary.get(interaction_type, 0) + 1
        
        return summary

    def _calculate_session_engagement_score(self, session, page_views, interactions) -> float:
        """Calculate engagement score for a specific session."""
        score = 0
        
        # Page views score (0-40 points)
        page_view_score = min(page_views.count() * 5, 40)
        score += page_view_score
        
        # Interaction score (0-40 points)
        interaction_score = min(interactions.count() * 10, 40)
        score += interaction_score
        
        # Duration score (0-20 points)
        if session.time_spent:
            duration_minutes = session.time_spent.total_seconds() / 60
            duration_score = min(duration_minutes * 2, 20)
            score += duration_score
        
        return min(score, 100)  # Cap at 100
