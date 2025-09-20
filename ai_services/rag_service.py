"""
Fixed RAG (Retrieval-Augmented Generation) Service using direct API calls.
"""

import requests
import logging
import time
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q

from .models import DocumentChunk, RAGQuery, EmbeddingCache
from .embedding_service import EmbeddingService
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation with similarity search and answer generation."""
    
    def __init__(self):
        # Initialize API key and headers
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            self.headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        else:
            self.api_key = None
            self.headers = None
            logger.warning("OpenAI API key not configured. RAG service will not work.")
        
        self.embedding_service = EmbeddingService()
        self.cache_service = CacheService()
        self.model = "gpt-3.5-turbo"
        self.max_context_tokens = 4000
        self.max_chunks = 5
        self.similarity_threshold = 0.7
        
    def query(self, question: str, context_type: Optional[str] = None, 
              source_id: Optional[str] = None, max_chunks: Optional[int] = None) -> Dict[str, Any]:
        """
        Main RAG query method that retrieves relevant context and generates an answer.
        
        Args:
            question: The user's question
            context_type: Type of context to search (profile, project, experience, etc.)
            source_id: Specific source ID to search within
            max_chunks: Maximum number of chunks to retrieve
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            if not self.api_key or not self.headers:
                return {
                    "answer": "I'm sorry, but the AI service is not available at the moment. Please try again later.",
                    "sources": [],
                    "metadata": {"error": "OpenAI API not configured"}
                }
            
            start_time = time.time()
            
            # Check cache first
            cache_key = self._get_query_cache_key(question, context_type, source_id)
            cached_result = self._get_cached_query(cache_key)
            if cached_result:
                logger.debug(f"Using cached result for query: {question[:50]}...")
                return cached_result
            
            # Get relevant chunks
            relevant_chunks = self._get_relevant_chunks(
                question, context_type, source_id, max_chunks or self.max_chunks
            )
            
            if not relevant_chunks:
                return {
                    "answer": "I don't have enough information to answer that question. Please try asking about my skills, projects, or experience.",
                    "sources": [],
                    "metadata": {"chunks_found": 0, "processing_time": time.time() - start_time}
                }
            
            # Prepare context
            context = self._prepare_context(relevant_chunks)
            
            # Generate answer
            answer = self._generate_answer(question, context)
            
            # Prepare sources
            sources = self._prepare_sources(relevant_chunks)
            
            # Create result
            result = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "chunks_found": len(relevant_chunks),
                    "context_length": len(context),
                    "processing_time": time.time() - start_time,
                    "model_used": self.model
                }
            }
            
            # Cache the result
            self._cache_query(cache_key, result)
            
            # Log the query
            self._log_query(question, context_type, source_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "sources": [],
                "metadata": {"error": str(e), "processing_time": time.time() - start_time}
            }
    
    def _get_relevant_chunks(self, question: str, context_type: Optional[str], 
                           source_id: Optional[str], max_chunks: int) -> List[DocumentChunk]:
        """Get relevant document chunks based on similarity to the question."""
        try:
            # Create embedding for the question
            question_embedding = self.embedding_service.create_embedding(question)
            
            # Build query
            query = DocumentChunk.objects.all()
            
            if context_type:
                query = query.filter(source_type=context_type)
            
            if source_id:
                query = query.filter(source_id=source_id)
            
            # Get all chunks (in a real implementation, you'd use vector similarity search)
            chunks = list(query[:100])  # Limit for performance
            
            if not chunks:
                return []
            
            # Calculate similarities (simplified - in production use proper vector DB)
            similarities = []
            for chunk in chunks:
                if chunk.embedding:
                    try:
                        chunk_embedding = json.loads(chunk.embedding)
                        similarity = self._cosine_similarity(question_embedding, chunk_embedding)
                        similarities.append((chunk, similarity))
                    except:
                        continue
            
            # Sort by similarity and return top chunks
            similarities.sort(key=lambda x: x[1], reverse=True)
            relevant_chunks = [chunk for chunk, sim in similarities[:max_chunks] if sim >= self.similarity_threshold]
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error getting relevant chunks: {str(e)}")
            return []
    
    def _prepare_context(self, chunks: List[DocumentChunk]) -> str:
        """Prepare context from relevant chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {i}] {chunk.content}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using OpenAI API."""
        try:
            # Prepare the prompt
            system_prompt = """You are a helpful AI assistant representing a developer's portfolio. 
            Use the provided context to answer questions about the developer's skills, projects, and experience. 
            Be professional, accurate, and helpful. If the context doesn't contain enough information, 
            say so politely."""
            
            user_prompt = f"""Context:
{context}

Question: {question}

Please provide a helpful answer based on the context above."""
            
            # Make API call
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            answer = result['choices'][0]['message']['content']
            
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I'm sorry, I couldn't generate an answer at the moment. Please try again."
    
    def _prepare_sources(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """Prepare source information for the answer."""
        sources = []
        
        for i, chunk in enumerate(chunks, 1):
            source = {
                "id": chunk.id,
                "title": chunk.source_title or f"Source {i}",
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "context_type": chunk.source_type,
                "source_id": chunk.source_id,
                "relevance_score": getattr(chunk, 'relevance_score', 0.0)
            }
            sources.append(source)
        
        return sources
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def _get_query_cache_key(self, question: str, context_type: Optional[str], source_id: Optional[str]) -> str:
        """Generate cache key for query."""
        key_parts = [question, context_type or "", source_id or ""]
        return f"rag_query_{hash('_'.join(key_parts))}"
    
    def _get_cached_query(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached query result."""
        try:
            return cache.get(cache_key)
        except:
            return None
    
    def _cache_query(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache query result."""
        try:
            cache.set(cache_key, result, timeout=3600)  # 1 hour
        except:
            pass
    
    def _log_query(self, question: str, context_type: Optional[str], source_id: Optional[str], result: Dict[str, Any]) -> None:
        """Log the query for analytics."""
        try:
            RAGQuery.objects.create(
                question=question,
                context_type=context_type or "general",
                source_id=source_id,
                answer=result.get("answer", "")[:1000],  # Truncate for storage
                chunks_used=result.get("metadata", {}).get("chunks_found", 0),
                processing_time=result.get("metadata", {}).get("processing_time", 0),
                success=True
            )
        except Exception as e:
            logger.warning(f"Error logging query: {e}")
