"""
Database Query Optimization Service
Provides optimized database queries with caching and performance monitoring.
"""

import logging
from typing import Any, Dict, List, Optional
from django.db import models, connection
from django.db.models import Prefetch, Q, F, Count, Avg, Max, Min, QuerySet
from django.core.cache import cache
from django.utils import timezone
from functools import wraps
import time

logger = logging.getLogger(__name__)


class QueryOptimizationService:
    """Service for optimizing database queries and providing cached results."""
    
    def __init__(self):
        self.cache_timeout = 1800  # 30 minutes
        self.stats_cache_timeout = 900  # 15 minutes
    
    def get_optimized_profiles(self, active_only: bool = True) -> QuerySet:
        """Get profiles with optimized queries."""
        try:
            queryset = models.QuerySet()
            
            # Import here to avoid circular imports
            from core.models import Profile
            
            queryset = Profile.objects.select_related().prefetch_related()
            
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Error getting optimized profiles: {str(e)}")
            return Profile.objects.none()
    
    def get_optimized_projects(self, featured_only: bool = False, 
                             status: str = None) -> QuerySet:
        """Get projects with optimized queries."""
        try:
            # Import here to avoid circular imports
            from projects.models import Project, ProjectImage
            
            queryset = Project.objects.select_related('profile').prefetch_related(
                Prefetch('images', queryset=ProjectImage.objects.order_by('order'))
            )
            
            if featured_only:
                queryset = queryset.filter(is_featured=True)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return queryset.order_by('-is_featured', 'order', '-created_at')
            
        except Exception as e:
            logger.error(f"Error getting optimized projects: {str(e)}")
            return Project.objects.none()
    
    def get_optimized_visitor_sessions(self, days: int = 30) -> QuerySet:
        """Get visitor sessions with optimized queries."""
        try:
            # Import here to avoid circular imports
            from visitors.models import VisitorSession, PageView, VisitorInteraction
            
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            
            queryset = VisitorSession.objects.filter(
                created_at__gte=cutoff_date
            ).prefetch_related(
                'pageviews',
                'visitorinteractions'
            ).order_by('-created_at')
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error getting optimized visitor sessions: {str(e)}")
            return VisitorSession.objects.none()
    
    def get_optimized_conversations(self, active_only: bool = True) -> QuerySet:
        """Get conversations with optimized queries."""
        try:
            # Import here to avoid circular imports
            from ai_chat.models import Conversation, Message
            
            queryset = Conversation.objects.select_related(
                'visitor_session', 'project'
            ).prefetch_related(
                Prefetch('messages', queryset=Message.objects.order_by('timestamp'))
            )
            
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Error getting optimized conversations: {str(e)}")
            return Conversation.objects.none()
    
    def get_optimized_job_analyses(self, days: int = 30) -> QuerySet:
        """Get job analyses with optimized queries."""
        try:
            # Import here to avoid circular imports
            from job_matching.models import JobAnalysis, SkillsMatch, JobRecommendation
            
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            
            queryset = JobAnalysis.objects.filter(
                created_at__gte=cutoff_date
            ).select_related('visitor_session').prefetch_related(
                'skillsmatch_set',
                'jobrecommendation_set'
            ).order_by('-created_at')
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error getting optimized job analyses: {str(e)}")
            return JobAnalysis.objects.none()
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get optimized project statistics."""
        try:
            cache_key = f"project_stats_{int(timezone.now().timestamp() // 900)}"  # 15-min cache
            
            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Import here to avoid circular imports
            from projects.models import Project
            
            stats = Project.objects.aggregate(
                total_projects=Count('id'),
                featured_projects=Count('id', filter=Q(is_featured=True)),
                completed_projects=Count('id', filter=Q(status='completed')),
                avg_complexity=Avg('complexity_score'),
                max_complexity=Max('complexity_score'),
                min_complexity=Min('complexity_score')
            )
            
            # Add status distribution
            status_dist = Project.objects.values('status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Add difficulty distribution
            difficulty_dist = Project.objects.values('difficulty_level').annotate(
                count=Count('id')
            ).order_by('-count')
            
            stats.update({
                'status_distribution': list(status_dist),
                'difficulty_distribution': list(difficulty_dist),
                'cached_at': timezone.now().isoformat()
            })
            
            # Cache the results
            cache.set(cache_key, stats, timeout=self.stats_cache_timeout)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting project statistics: {str(e)}")
            return {}
    
    def get_visitor_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get optimized visitor statistics."""
        try:
            cache_key = f"visitor_stats_{days}_{int(timezone.now().timestamp() // 300)}"  # 5-min cache
            
            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Import here to avoid circular imports
            from visitors.models import VisitorSession, PageView, VisitorInteraction
            
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            
            # Basic session stats
            session_stats = VisitorSession.objects.filter(
                created_at__gte=cutoff_date
            ).aggregate(
                total_sessions=Count('id'),
                unique_visitors=Count('session_key', distinct=True),
                avg_page_views=Avg('page_views_count'),
                total_page_views=Count('page_views')
            )
            
            # Device and browser distribution
            device_dist = VisitorSession.objects.filter(
                created_at__gte=cutoff_date
            ).values('device_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            browser_dist = VisitorSession.objects.filter(
                created_at__gte=cutoff_date
            ).values('browser').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Interaction stats
            interaction_stats = VisitorInteraction.objects.filter(
                visitor_session__created_at__gte=cutoff_date
            ).values('interaction_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            stats = {
                **session_stats,
                'device_distribution': list(device_dist),
                'browser_distribution': list(browser_dist),
                'interaction_distribution': list(interaction_stats),
                'period_days': days,
                'cached_at': timezone.now().isoformat()
            }
            
            # Cache the results
            cache.set(cache_key, stats, timeout=self.stats_cache_timeout)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting visitor statistics: {str(e)}")
            return {}
    
    def get_conversation_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get optimized conversation statistics."""
        try:
            cache_key = f"conversation_stats_{days}_{int(timezone.now().timestamp() // 300)}"  # 5-min cache
            
            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Import here to avoid circular imports
            from ai_chat.models import Conversation, Message
            
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            
            # Basic conversation stats
            conversation_stats = Conversation.objects.filter(
                created_at__gte=cutoff_date
            ).aggregate(
                total_conversations=Count('id'),
                active_conversations=Count('id', filter=Q(is_active=True)),
                avg_messages_per_conversation=Avg('messages__id')
            )
            
            # Context type distribution
            context_dist = Conversation.objects.filter(
                created_at__gte=cutoff_date
            ).values('context_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Message stats
            message_stats = Message.objects.filter(
                conversation__created_at__gte=cutoff_date
            ).aggregate(
                total_messages=Count('id'),
                user_messages=Count('id', filter=Q(is_user=True)),
                ai_messages=Count('id', filter=Q(is_user=False)),
                avg_response_time=Avg('response_time')
            )
            
            stats = {
                **conversation_stats,
                **message_stats,
                'context_distribution': list(context_dist),
                'period_days': days,
                'cached_at': timezone.now().isoformat()
            }
            
            # Cache the results
            cache.set(cache_key, stats, timeout=self.stats_cache_timeout)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting conversation statistics: {str(e)}")
            return {}
    
    def get_job_analysis_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get optimized job analysis statistics."""
        try:
            cache_key = f"job_analysis_stats_{days}_{int(timezone.now().timestamp() // 300)}"  # 5-min cache
            
            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Import here to avoid circular imports
            from job_matching.models import JobAnalysis
            
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            
            # Basic analysis stats
            analysis_stats = JobAnalysis.objects.filter(
                created_at__gte=cutoff_date
            ).aggregate(
                total_analyses=Count('id'),
                avg_overall_score=Avg('overall_match_score'),
                avg_skills_score=Avg('skills_match_score'),
                avg_experience_score=Avg('experience_match_score'),
                avg_education_score=Avg('education_match_score'),
                avg_processing_time=Avg('processing_time')
            )
            
            # Match level distribution (using score ranges)
            match_dist = [
                {
                    'match_level': 'excellent',
                    'count': JobAnalysis.objects.filter(
                        created_at__gte=cutoff_date,
                        overall_match_score__gte=90
                    ).count()
                },
                {
                    'match_level': 'good',
                    'count': JobAnalysis.objects.filter(
                        created_at__gte=cutoff_date,
                        overall_match_score__gte=70,
                        overall_match_score__lt=90
                    ).count()
                },
                {
                    'match_level': 'fair',
                    'count': JobAnalysis.objects.filter(
                        created_at__gte=cutoff_date,
                        overall_match_score__gte=50,
                        overall_match_score__lt=70
                    ).count()
                },
                {
                    'match_level': 'poor',
                    'count': JobAnalysis.objects.filter(
                        created_at__gte=cutoff_date,
                        overall_match_score__lt=50
                    ).count()
                }
            ]
            
            stats = {
                **analysis_stats,
                'match_level_distribution': match_dist,
                'period_days': days,
                'cached_at': timezone.now().isoformat()
            }
            
            # Cache the results
            cache.set(cache_key, stats, timeout=self.stats_cache_timeout)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting job analysis statistics: {str(e)}")
            return {}
    
    def get_database_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        try:
            cache_key = f"db_performance_{int(timezone.now().timestamp() // 60)}"  # 1-min cache
            
            # Try cache first
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            with connection.cursor() as cursor:
                # Get connection info
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()[0]
                
                # Get table sizes (if PostgreSQL)
                if 'postgresql' in db_version.lower():
                    cursor.execute("""
                        SELECT schemaname, tablename, 
                               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                    """)
                    table_sizes = cursor.fetchall()
                else:
                    table_sizes = []
                
                # Get connection count
                cursor.execute("SELECT count(*) FROM pg_stat_activity;")
                connection_count = cursor.fetchone()[0] if 'postgresql' in db_version.lower() else 0
            
            stats = {
                'database_version': db_version,
                'table_sizes': table_sizes,
                'connection_count': connection_count,
                'cached_at': timezone.now().isoformat()
            }
            
            # Cache the results
            cache.set(cache_key, stats, timeout=60)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database performance stats: {str(e)}")
            return {}
    
    def optimize_queryset(self, queryset: QuerySet, prefetch_relations: List[str] = None,
                         select_relations: List[str] = None) -> QuerySet:
        """Apply optimizations to a queryset."""
        try:
            if select_relations:
                queryset = queryset.select_related(*select_relations)
            
            if prefetch_relations:
                queryset = queryset.prefetch_related(*prefetch_relations)
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error optimizing queryset: {str(e)}")
            return queryset
    
    def clear_query_cache(self, cache_pattern: str = None) -> int:
        """Clear query-related cache entries."""
        try:
            if cache_pattern:
                # Clear specific pattern
                logger.info(f"Clearing query cache for pattern: {cache_pattern}")
                return 0  # Simplified - in production you'd implement pattern-based clearing
            else:
                # Clear all query cache
                cache.clear()
                logger.info("Cleared all query cache")
                return 1
                
        except Exception as e:
            logger.error(f"Error clearing query cache: {str(e)}")
            return 0


def monitor_query_performance(func):
    """Decorator to monitor query performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log slow queries
            logger.warning(f"Slow query detected in {func.__name__}: {execution_time:.2f}s")
        
        return result
    
    return wrapper


# Global query optimization service instance
query_optimizer = QueryOptimizationService()
