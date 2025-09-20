"""
Cache Service for AI Services
Manages caching of embeddings, RAG queries, and other AI-related data.
"""

import logging
import json
import hashlib
from typing import Any, Dict, List, Optional
from django.core.cache import cache
from django.utils import timezone
from .models import EmbeddingCache, RAGQuery
import time

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing AI-related caching operations."""
    
    def __init__(self):
        self.default_timeout = 86400  # 24 hours
        self.embedding_timeout = 86400 * 7  # 7 days
        self.rag_timeout = 3600  # 1 hour
    
    def cache_embedding(self, text: str, embedding: List[float], model: str = "text-embedding-ada-002") -> str:
        """Cache an embedding with its text content."""
        try:
            cache_key = self._get_embedding_cache_key(text)
            
            # Cache in Redis
            cache_data = {
                'embedding': embedding,
                'text': text[:1000],  # Store first 1000 chars
                'model': model,
                'cached_at': timezone.now().isoformat()
            }
            cache.set(cache_key, cache_data, timeout=self.embedding_timeout)
            
            # Cache in database for longer term storage
            text_hash = self._hash_text(text)
            EmbeddingCache.objects.update_or_create(
                text_hash=text_hash,
                defaults={
                    'text_content': text[:1000],
                    'embedding': json.dumps(embedding),
                    'model_name': model,
                    'token_count': len(text.split()),
                    'created_at': timezone.now()
                }
            )
            
            logger.debug(f"Cached embedding for text: {text[:50]}...")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching embedding: {str(e)}")
            raise
    
    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        try:
            cache_key = self._get_embedding_cache_key(text)
            
            # Try Redis cache first
            cached_data = cache.get(cache_key)
            if cached_data and 'embedding' in cached_data:
                logger.debug(f"Retrieved embedding from Redis cache: {text[:50]}...")
                return cached_data['embedding']
            
            # Try database cache
            text_hash = self._hash_text(text)
            embedding_cache = EmbeddingCache.objects.filter(
                text_hash=text_hash
            ).first()
            
            if embedding_cache:
                # Update Redis cache
                embedding_vector = json.loads(embedding_cache.embedding)
                cache_data = {
                    'embedding': embedding_vector,
                    'text': embedding_cache.text_content,
                    'model': embedding_cache.model_name,
                    'cached_at': embedding_cache.created_at.isoformat()
                }
                cache.set(cache_key, cache_data, timeout=self.embedding_timeout)
                
                logger.debug(f"Retrieved embedding from database cache: {text[:50]}...")
                return embedding_vector
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached embedding: {str(e)}")
            return None
    
    def cache_rag_query(self, query: str, response: Dict[str, Any], context_type: str = None) -> str:
        """Cache a RAG query and response."""
        try:
            cache_key = self._get_rag_cache_key(query, context_type)
            
            # Cache in Redis
            cache_data = {
                'query': query,
                'response': response,
                'context_type': context_type,
                'cached_at': timezone.now().isoformat()
            }
            cache.set(cache_key, cache_data, timeout=self.rag_timeout)
            
            # Cache in database for analytics
            RAGQuery.objects.create(
                query_text=query,
                context_type=context_type or 'general',
                response_generated=response.get('answer', ''),
                confidence_score=response.get('confidence', 0),
                chunks_used=response.get('chunks_used', []),
                tokens_used=response.get('tokens_used', 0),
                processing_time=response.get('response_time', 0)
            )
            
            logger.debug(f"Cached RAG query: {query[:50]}...")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching RAG query: {str(e)}")
            raise
    
    def get_cached_rag_query(self, query: str, context_type: str = None) -> Optional[Dict[str, Any]]:
        """Get cached RAG query response."""
        try:
            cache_key = self._get_rag_cache_key(query, context_type)
            
            cached_data = cache.get(cache_key)
            if cached_data and 'response' in cached_data:
                logger.debug(f"Retrieved RAG query from cache: {query[:50]}...")
                return cached_data['response']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached RAG query: {str(e)}")
            return None
    
    def cache_job_analysis(self, job_text: str, analysis_result: Dict[str, Any]) -> str:
        """Cache job analysis result."""
        try:
            cache_key = self._get_job_analysis_cache_key(job_text)
            
            cache_data = {
                'job_text': job_text[:1000],  # Store first 1000 chars
                'analysis': analysis_result,
                'cached_at': timezone.now().isoformat()
            }
            cache.set(cache_key, cache_data, timeout=self.default_timeout)
            
            logger.debug(f"Cached job analysis: {job_text[:50]}...")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching job analysis: {str(e)}")
            raise
    
    def get_cached_job_analysis(self, job_text: str) -> Optional[Dict[str, Any]]:
        """Get cached job analysis result."""
        try:
            cache_key = self._get_job_analysis_cache_key(job_text)
            
            cached_data = cache.get(cache_key)
            if cached_data and 'analysis' in cached_data:
                logger.debug(f"Retrieved job analysis from cache: {job_text[:50]}...")
                return cached_data['analysis']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached job analysis: {str(e)}")
            return None
    
    def cache_chat_response(self, conversation_id: str, message: str, response: str) -> str:
        """Cache chat response for conversation continuity."""
        try:
            cache_key = f"chat:{conversation_id}:{self._hash_text(message)}"
            
            cache_data = {
                'message': message,
                'response': response,
                'cached_at': timezone.now().isoformat()
            }
            cache.set(cache_key, cache_data, timeout=3600)  # 1 hour
            
            logger.debug(f"Cached chat response for conversation {conversation_id}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching chat response: {str(e)}")
            raise
    
    def get_cached_chat_response(self, conversation_id: str, message: str) -> Optional[str]:
        """Get cached chat response."""
        try:
            cache_key = f"chat:{conversation_id}:{self._hash_text(message)}"
            
            cached_data = cache.get(cache_key)
            if cached_data and 'response' in cached_data:
                logger.debug(f"Retrieved chat response from cache for conversation {conversation_id}")
                return cached_data['response']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached chat response: {str(e)}")
            return None
    
    def clear_cache(self, cache_type: str = None) -> int:
        """Clear cache entries."""
        try:
            if cache_type == 'embeddings':
                # Clear embedding cache (delete old entries)
                old_entries = EmbeddingCache.objects.filter(
                    created_at__lt=timezone.now() - timezone.timedelta(days=30)
                )
                count = old_entries.count()
                old_entries.delete()
                return count
            
            elif cache_type == 'rag':
                # Clear RAG query cache (Redis only)
                # Note: This is a simplified approach - in production you'd want more sophisticated cache clearing
                return 0
            
            elif cache_type == 'all':
                # Clear all caches
                cache.clear()
                EmbeddingCache.objects.filter(is_active=True).update(is_active=False)
                return EmbeddingCache.objects.filter(is_active=False).count()
            
            else:
                # Clear Redis cache only
                cache.clear()
                return 0
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = {
                'embedding_cache': {
                    'total_entries': EmbeddingCache.objects.count(),
                    'recent_entries': EmbeddingCache.objects.filter(
                        created_at__gte=timezone.now() - timezone.timedelta(days=7)
                    ).count()
                },
                'rag_queries': {
                    'total_queries': RAGQuery.objects.count(),
                    'recent_queries': RAGQuery.objects.filter(
                        created_at__gte=timezone.now() - timezone.timedelta(days=7)
                    ).count(),
                    'avg_processing_time': self._get_avg_processing_time(),
                    'avg_confidence': self._get_avg_confidence()
                },
                'cache_settings': {
                    'embedding_timeout': self.embedding_timeout,
                    'rag_timeout': self.rag_timeout,
                    'default_timeout': self.default_timeout
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def _get_embedding_cache_key(self, text: str) -> str:
        """Generate cache key for embedding."""
        text_hash = self._hash_text(text)
        return f"embedding:{text_hash}"
    
    def _get_rag_cache_key(self, query: str, context_type: str = None) -> str:
        """Generate cache key for RAG query."""
        query_hash = self._hash_text(query)
        context_suffix = f":{context_type}" if context_type else ""
        return f"rag:{query_hash}{context_suffix}"
    
    def _get_job_analysis_cache_key(self, job_text: str) -> str:
        """Generate cache key for job analysis."""
        text_hash = self._hash_text(job_text)
        return f"job_analysis:{text_hash}"
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_avg_processing_time(self) -> float:
        """Get average processing time for RAG queries."""
        try:
            from django.db.models import Avg
            avg_time = RAGQuery.objects.aggregate(
                avg_time=Avg('processing_time')
            )['avg_time']
            return round(avg_time, 2) if avg_time else 0.0
        except:
            return 0.0
    
    def _get_avg_confidence(self) -> float:
        """Get average confidence score for RAG queries."""
        try:
            from django.db.models import Avg
            avg_confidence = RAGQuery.objects.aggregate(
                avg_confidence=Avg('confidence_score')
            )['avg_confidence']
            return round(avg_confidence, 2) if avg_confidence else 0.0
        except:
            return 0.0
    
    def get_rag_query_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached RAG query response by cache key."""
        try:
            cached_data = cache.get(cache_key)
            if cached_data and 'response' in cached_data:
                logger.debug(f"Retrieved RAG query from cache: {cache_key}")
                return cached_data['response']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached RAG query: {str(e)}")
            return None
    
    def set_rag_query_cache(self, cache_key: str, response: Dict[str, Any]) -> str:
        """Cache a RAG query response by cache key."""
        try:
            cache_data = {
                'response': response,
                'cached_at': timezone.now().isoformat()
            }
            cache.set(cache_key, cache_data, timeout=self.rag_timeout)
            
            logger.debug(f"Cached RAG query response: {cache_key}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Error caching RAG query response: {str(e)}")
            raise
    
    def cleanup_old_cache(self, days_old: int = 30) -> int:
        """Clean up old cache entries."""
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
            
            # Clean up old embedding cache entries
            old_embeddings = EmbeddingCache.objects.filter(
                created_at__lt=cutoff_date
            )
            count = old_embeddings.count()
            old_embeddings.delete()
            
            # Clean up old RAG queries (keep for analytics)
            # Note: In production, you might want to archive these instead of deleting
            
            logger.info(f"Cleaned up {count} old cache entries")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up old cache: {str(e)}")
            return 0
