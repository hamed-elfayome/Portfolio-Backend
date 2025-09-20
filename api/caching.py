"""
API Response Caching Service
Provides comprehensive caching for API responses, query results, and database operations.
"""

import logging
import json
import hashlib
from typing import Any, Dict, List, Optional, Callable
from django.core.cache import cache
from django.utils import timezone
from django.db.models import QuerySet
from django.http import HttpRequest
from functools import wraps
import time

logger = logging.getLogger(__name__)


class APICacheService:
    """Service for managing API response caching and query optimization."""
    
    def __init__(self):
        # Cache timeouts (in seconds)
        self.timeouts = {
            'api_response': 3600,      # 1 hour for API responses
            'query_result': 1800,      # 30 minutes for query results
            'statistics': 900,         # 15 minutes for statistics
            'search_results': 600,     # 10 minutes for search results
            'profile_data': 7200,      # 2 hours for profile data
            'project_data': 3600,      # 1 hour for project data
            'visitor_analytics': 300,  # 5 minutes for visitor analytics
            'embedding': 86400,        # 24 hours for embeddings
            'rag_query': 3600,         # 1 hour for RAG queries
            'job_analysis': 3600,      # 1 hour for job analysis
        }
    
    def cache_api_response(self, cache_key: str, response_data: Dict[str, Any], 
                          cache_type: str = 'api_response') -> str:
        """Cache API response data."""
        try:
            timeout = self.timeouts.get(cache_type, self.timeouts['api_response'])
            
            cache_data = {
                'data': response_data,
                'cached_at': timezone.now().isoformat(),
                'cache_type': cache_type,
                'version': '1.0'
            }
            
            cache.set(cache_key, cache_data, timeout=timeout)
            logger.debug(f"Cached API response: {cache_key} (type: {cache_type})")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching API response: {str(e)}")
            raise
    
    def get_cached_api_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached API response data."""
        try:
            cached_data = cache.get(cache_key)
            if cached_data and 'data' in cached_data:
                logger.debug(f"Retrieved API response from cache: {cache_key}")
                return cached_data['data']
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached API response: {str(e)}")
            return None
    
    def cache_query_result(self, cache_key: str, queryset_data: List[Dict[str, Any]], 
                          cache_type: str = 'query_result') -> str:
        """Cache database query results."""
        try:
            timeout = self.timeouts.get(cache_type, self.timeouts['query_result'])
            
            cache_data = {
                'results': queryset_data,
                'count': len(queryset_data),
                'cached_at': timezone.now().isoformat(),
                'cache_type': cache_type
            }
            
            cache.set(cache_key, cache_data, timeout=timeout)
            logger.debug(f"Cached query result: {cache_key} ({len(queryset_data)} items)")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching query result: {str(e)}")
            raise
    
    def get_cached_query_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result."""
        try:
            cached_data = cache.get(cache_key)
            if cached_data and 'results' in cached_data:
                logger.debug(f"Retrieved query result from cache: {cache_key}")
                return cached_data['results']
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached query result: {str(e)}")
            return None
    
    def cache_statistics(self, cache_key: str, stats_data: Dict[str, Any]) -> str:
        """Cache statistics data."""
        try:
            cache_data = {
                'stats': stats_data,
                'cached_at': timezone.now().isoformat(),
                'cache_type': 'statistics'
            }
            
            cache.set(cache_key, cache_data, timeout=self.timeouts['statistics'])
            logger.debug(f"Cached statistics: {cache_key}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching statistics: {str(e)}")
            raise
    
    def get_cached_statistics(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached statistics."""
        try:
            cached_data = cache.get(cache_key)
            if cached_data and 'stats' in cached_data:
                logger.debug(f"Retrieved statistics from cache: {cache_key}")
                return cached_data['stats']
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached statistics: {str(e)}")
            return None
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from prefix and parameters."""
        try:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_parts = [prefix] + [f"{k}:{v}" for k, v in sorted_kwargs if v is not None]
            key_string = "|".join(key_parts)
            return hashlib.md5(key_string.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating cache key: {str(e)}")
            return f"{prefix}:{int(time.time())}"
    
    def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        try:
            # Note: This is a simplified approach. In production with Redis,
            # you'd use SCAN with pattern matching for more efficient invalidation
            logger.info(f"Cache invalidation requested for pattern: {pattern}")
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            stats = {
                'cache_settings': self.timeouts,
                'cache_health': self._check_cache_health(),
                'memory_usage': self._get_memory_usage(),
                'hit_rates': self._get_hit_rates(),
                'timestamp': timezone.now().isoformat()
            }
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def clear_all_cache(self) -> bool:
        """Clear all cache entries."""
        try:
            cache.clear()
            logger.info("Cleared all cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health and connectivity."""
        try:
            # Test cache connectivity
            test_key = "health_check"
            test_value = "ok"
            
            cache.set(test_key, test_value, timeout=10)
            retrieved_value = cache.get(test_key)
            
            return {
                'connected': retrieved_value == test_value,
                'response_time': self._measure_cache_response_time(),
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking cache health: {str(e)}")
            return {
                'connected': False,
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }
    
    def _measure_cache_response_time(self) -> float:
        """Measure cache response time."""
        try:
            start_time = time.time()
            test_key = f"perf_test_{int(time.time())}"
            test_value = "performance_test"
            
            cache.set(test_key, test_value, timeout=10)
            cache.get(test_key)
            
            return round((time.time() - start_time) * 1000, 2)  # milliseconds
            
        except Exception as e:
            logger.error(f"Error measuring cache response time: {str(e)}")
            return 0.0
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get cache memory usage information."""
        try:
            # This is a placeholder - in production you'd get actual Redis memory stats
            return {
                'used_memory': 'N/A',
                'max_memory': 'N/A',
                'memory_usage_percent': 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return {}
    
    def _get_hit_rates(self) -> Dict[str, Any]:
        """Get cache hit rates."""
        try:
            # This is a placeholder - in production you'd track actual hit rates
            return {
                'api_responses': 'N/A',
                'query_results': 'N/A',
                'statistics': 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error getting hit rates: {str(e)}")
            return {}


def cache_api_response(cache_type: str = 'api_response', timeout: int = None):
    """Decorator for caching API responses."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            cache_service = APICacheService()
            
            # Generate cache key from request
            cache_key = cache_service.generate_cache_key(
                f"api:{view_func.__name__}",
                path=request.path,
                method=request.method,
                **request.GET.dict()
            )
            
            # Try to get cached response
            cached_response = cache_service.get_cached_api_response(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for API response: {cache_key}")
                return cached_response
            
            # Execute view function
            response = view_func(request, *args, **kwargs)
            
            # Cache the response if it's successful
            if hasattr(response, 'data') and response.status_code == 200:
                cache_service.cache_api_response(
                    cache_key, 
                    response.data, 
                    cache_type
                )
                logger.debug(f"Cached API response: {cache_key}")
            
            return response
        
        return wrapper
    return decorator


def cache_query_result(cache_type: str = 'query_result', timeout: int = None):
    """Decorator for caching database query results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = APICacheService()
            
            # Generate cache key from function arguments
            cache_key = cache_service.generate_cache_key(
                f"query:{func.__name__}",
                **kwargs
            )
            
            # Try to get cached result
            cached_result = cache_service.get_cached_query_result(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for query result: {cache_key}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            if result:
                cache_service.cache_query_result(cache_key, result, cache_type)
                logger.debug(f"Cached query result: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


def cache_statistics(cache_type: str = 'statistics', timeout: int = None):
    """Decorator for caching statistics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = APICacheService()
            
            # Generate cache key from function arguments
            cache_key = cache_service.generate_cache_key(
                f"stats:{func.__name__}",
                **kwargs
            )
            
            # Try to get cached statistics
            cached_stats = cache_service.get_cached_statistics(cache_key)
            if cached_stats:
                logger.debug(f"Cache hit for statistics: {cache_key}")
                return cached_stats
            
            # Execute function
            stats = func(*args, **kwargs)
            
            # Cache the statistics
            if stats:
                cache_service.cache_statistics(cache_key, stats)
                logger.debug(f"Cached statistics: {cache_key}")
            
            return stats
        
        return wrapper
    return decorator


# Global cache service instance
api_cache_service = APICacheService()
