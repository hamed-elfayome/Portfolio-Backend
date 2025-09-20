"""
Optimized RAG (Retrieval-Augmented Generation) Service
Implements high-performance similarity search with database optimization and caching.
"""

from openai import OpenAI
import logging
import time
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.db import connection

from .models import DocumentChunk, RAGQuery, EmbeddingCache
from .embedding_service import EmbeddingService
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class OptimizedRAGService:
    """Optimized service for Retrieval-Augmented Generation with high-performance similarity search."""
    
    def __init__(self):
        # Initialize OpenAI client only if API key is available
        api_key = settings.OPENAI_API_KEY
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured. RAG service will not work.")
        
        self.embedding_service = EmbeddingService()
        self.cache_service = CacheService()
        self.model = "gpt-3.5-turbo"
        self.max_context_tokens = 4000
        self.max_chunks = 5
        self.similarity_threshold = 0.7
        self.batch_size = 100  # Process embeddings in batches
        
    def query(self, question: str, context_type: Optional[str] = None, 
              source_id: Optional[str] = None, max_chunks: Optional[int] = None) -> Dict[str, Any]:
        """
        Main RAG query method with optimized performance.
        """
        start_time = time.time()
        
        try:
            if not self.client:
                return self._fallback_response("AI service is not configured. Please try again later.")
            
            # Check cache first
            cache_key = self._get_query_cache_key(question, context_type, source_id)
            cached_result = self.cache_service.get_rag_query_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached RAG response for: {question[:50]}...")
                return cached_result
            
            # Step 1: Optimized similarity search
            relevant_chunks = self.optimized_similarity_search(
                question, context_type, source_id, max_chunks or self.max_chunks
            )
            
            if not relevant_chunks:
                return self._fallback_response("I couldn't find relevant information to answer your question.")
            
            # Step 2: Prepare context
            context = self._prepare_context(relevant_chunks, question)
            
            # Step 3: Generate answer
            answer_result = self._generate_answer(question, context, relevant_chunks)
            
            # Step 4: Calculate confidence
            confidence = self._calculate_confidence(answer_result, relevant_chunks)
            
            # Step 5: Prepare response
            processing_time = time.time() - start_time
            response = {
                'answer': answer_result['answer'],
                'confidence': confidence,
                'response_time': processing_time,
                'chunks_used': [chunk.chunk_id for chunk in relevant_chunks],
                'chunks_retrieved': len(relevant_chunks),
                'context_type': context_type,
                'source_id': source_id,
                'tokens_used': answer_result.get('tokens_used', 0),
                'model_used': self.model
            }
            
            # Step 6: Cache the result
            self.cache_service.set_rag_query_cache(cache_key, response)
            
            # Step 7: Log the query
            self._log_rag_query(question, context_type, source_id, relevant_chunks, 
                              answer_result, confidence, processing_time)
            
            logger.info(f"Optimized RAG query completed in {processing_time:.2f}s with confidence {confidence:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"Error in optimized RAG query: {str(e)}")
            return self._fallback_response("I encountered an error while processing your question. Please try again.")
    
    def optimized_similarity_search(self, query: str, context_type: Optional[str] = None, 
                                  source_id: Optional[str] = None, limit: int = 5) -> List[DocumentChunk]:
        """
        Optimized similarity search with database-level filtering and batch processing.
        """
        try:
            # Create embedding for the query
            query_embedding = self.embedding_service.create_embedding(query)
            if not query_embedding:
                logger.error("Failed to create query embedding")
                return []
            
            # Build optimized queryset with database-level filtering
            queryset = DocumentChunk.objects.filter(
                is_active=True,
                embedding__isnull=False
            ).exclude(embedding='')
            
            # Apply filters at database level
            if context_type:
                queryset = queryset.filter(source_type=context_type)
            if source_id:
                queryset = queryset.filter(source_id=source_id)
            
            # Use database indexes for ordering and limiting
            queryset = queryset.order_by('-created_at')[:limit * 3]  # Get 3x more for filtering
            
            # Convert to list for processing
            chunks = list(queryset)
            if not chunks:
                logger.warning(f"No chunks found for context_type={context_type}, source_id={source_id}")
                return []
            
            # Batch process similarities for better performance
            chunk_similarities = self._batch_calculate_similarities(query_embedding, chunks)
            
            # Filter by threshold and sort
            filtered_similarities = [
                (chunk, similarity) for chunk, similarity in chunk_similarities
                if similarity >= self.similarity_threshold
            ]
            
            # Sort by similarity and return top results
            filtered_similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunks = [chunk for chunk, similarity in filtered_similarities[:limit]]
            
            logger.info(f"Found {len(top_chunks)} relevant chunks for query: {query[:50]}...")
            return top_chunks
            
        except Exception as e:
            logger.error(f"Error in optimized similarity search: {str(e)}")
            return []
    
    def _batch_calculate_similarities(self, query_embedding: List[float], chunks: List[DocumentChunk]) -> List[Tuple[DocumentChunk, float]]:
        """
        Calculate similarities in batches for better performance.
        """
        similarities = []
        
        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            
            # Extract embeddings for this batch
            batch_embeddings = []
            valid_chunks = []
            
            for chunk in batch:
                chunk_embedding = chunk.get_embedding_vector()
                if chunk_embedding and len(chunk_embedding) == len(query_embedding):
                    batch_embeddings.append(chunk_embedding)
                    valid_chunks.append(chunk)
            
            if not batch_embeddings:
                continue
            
            # Vectorized similarity calculation
            try:
                query_array = np.array(query_embedding)
                batch_array = np.array(batch_embeddings)
                
                # Calculate cosine similarities using vectorized operations
                dot_products = np.dot(batch_array, query_array)
                norms = np.linalg.norm(batch_array, axis=1) * np.linalg.norm(query_array)
                
                # Avoid division by zero
                valid_norms = norms > 0
                batch_similarities = np.zeros(len(batch_embeddings))
                batch_similarities[valid_norms] = dot_products[valid_norms] / norms[valid_norms]
                
                # Add to results
                for chunk, similarity in zip(valid_chunks, batch_similarities):
                    similarities.append((chunk, float(similarity)))
                    
            except Exception as e:
                logger.error(f"Error in batch similarity calculation: {str(e)}")
                # Fallback to individual calculations
                for chunk in valid_chunks:
                    chunk_embedding = chunk.get_embedding_vector()
                    similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                    similarities.append((chunk, similarity))
        
        return similarities
    
    def _prepare_context(self, chunks: List[DocumentChunk], question: str) -> str:
        """Prepare context from retrieved chunks for answer generation."""
        try:
            context_parts = []
            total_tokens = 0
            
            for i, chunk in enumerate(chunks):
                # Add chunk content with source information
                chunk_context = f"[Source: {chunk.get_source_type_display()}"
                if chunk.source_title:
                    chunk_context += f" - {chunk.source_title}"
                chunk_context += f"]\n{chunk.content}\n"
                
                # Estimate token count (rough approximation)
                chunk_tokens = len(chunk.content.split()) * 1.3  # Rough token estimation
                
                if total_tokens + chunk_tokens > self.max_context_tokens:
                    break
                
                context_parts.append(chunk_context)
                total_tokens += chunk_tokens
            
            context = "\n".join(context_parts)
            
            # Add instruction
            context = f"""Based on the following information about the developer's portfolio:

{context}

Please answer the following question using only the information provided above. If the information doesn't contain enough detail to answer the question, please say so."""
            
            logger.debug(f"Prepared context with {len(context_parts)} chunks, ~{total_tokens:.0f} tokens")
            return context
            
        except Exception as e:
            logger.error(f"Error preparing context: {str(e)}")
            return ""
    
    def _generate_answer(self, question: str, context: str, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Generate answer using OpenAI API with the prepared context."""
        try:
            # Prepare system message
            system_message = """You are an AI assistant representing a developer's portfolio. Your role is to answer questions about the developer's skills, experience, and projects based on the provided context.

Guidelines:
- Answer based only on the information provided in the context
- Be helpful, professional, and accurate
- If you don't have enough information, say so clearly
- Highlight relevant skills, experience, and achievements
- Keep responses concise but informative
- Use a friendly, professional tone"""
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"{context}\n\nQuestion: {question}"}
            ]
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                top_p=0.9
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"Generated answer using {tokens_used} tokens")
            
            return {
                'answer': answer,
                'tokens_used': tokens_used,
                'model_used': self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'answer': "I'm sorry, I encountered an error while generating a response. Please try again.",
                'tokens_used': 0,
                'model_used': self.model
            }
    
    def _calculate_confidence(self, answer_result: Dict[str, Any], chunks: List[DocumentChunk]) -> float:
        """Calculate confidence score based on answer quality and chunk relevance."""
        try:
            base_confidence = 0.5
            
            # Factor 1: Number of relevant chunks
            chunk_factor = min(len(chunks) / self.max_chunks, 1.0) * 0.3
            
            # Factor 2: Answer length (longer answers often indicate more confidence)
            answer_length = len(answer_result.get('answer', ''))
            length_factor = min(answer_length / 200, 1.0) * 0.2
            
            # Factor 3: Tokens used (more tokens might indicate more detailed response)
            tokens_used = answer_result.get('tokens_used', 0)
            token_factor = min(tokens_used / 300, 1.0) * 0.2
            
            # Factor 4: Check for uncertainty indicators in the answer
            answer_text = answer_result.get('answer', '').lower()
            uncertainty_indicators = ['not sure', 'unclear', 'don\'t know', 'insufficient', 'limited information']
            uncertainty_factor = 0.1 if any(indicator in answer_text for indicator in uncertainty_indicators) else 0.0
            
            confidence = base_confidence + chunk_factor + length_factor + token_factor - uncertainty_factor
            confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def _get_query_cache_key(self, question: str, context_type: Optional[str], source_id: Optional[str]) -> str:
        """Generate cache key for RAG query."""
        import hashlib
        
        # Create a normalized version of the query
        normalized_question = question.lower().strip()
        cache_string = f"{normalized_question}:{context_type or 'all'}:{source_id or 'all'}"
        cache_hash = hashlib.md5(cache_string.encode('utf-8')).hexdigest()
        return f"rag_query_optimized:{cache_hash}"
    
    def _log_rag_query(self, question: str, context_type: Optional[str], source_id: Optional[str],
                      chunks: List[DocumentChunk], answer_result: Dict[str, Any], 
                      confidence: float, processing_time: float):
        """Log RAG query to database for analytics."""
        try:
            RAGQuery.objects.create(
                query_text=question,
                context_type=context_type or '',
                source_id=source_id or '',
                chunks_retrieved=[chunk.chunk_id for chunk in chunks],
                chunks_used=[chunk.chunk_id for chunk in chunks],
                similarity_scores=[],  # Could be enhanced to store actual scores
                response_generated=answer_result.get('answer', ''),
                confidence_score=confidence,
                tokens_used=answer_result.get('tokens_used', 0),
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"Error logging RAG query: {str(e)}")
    
    def _fallback_response(self, message: str) -> Dict[str, Any]:
        """Return a fallback response when the service is unavailable."""
        return {
            'answer': message,
            'confidence': 0.0,
            'response_time': 0.0,
            'chunks_used': [],
            'chunks_retrieved': 0,
            'context_type': None,
            'source_id': None,
            'tokens_used': 0,
            'model_used': 'fallback'
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the optimized RAG service."""
        try:
            # Get recent query performance
            recent_queries = RAGQuery.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-created_at')[:100]
            
            if not recent_queries:
                return {'message': 'No recent queries found'}
            
            # Calculate performance metrics
            processing_times = [q.processing_time for q in recent_queries if q.processing_time]
            confidence_scores = [q.confidence_score for q in recent_queries if q.confidence_score]
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Get database statistics
            total_chunks = DocumentChunk.objects.filter(is_active=True).count()
            chunks_with_embeddings = DocumentChunk.objects.filter(
                is_active=True, 
                embedding__isnull=False
            ).exclude(embedding='').count()
            
            return {
                'total_queries_analyzed': len(recent_queries),
                'average_processing_time': round(avg_processing_time, 3),
                'average_confidence': round(avg_confidence, 3),
                'total_active_chunks': total_chunks,
                'chunks_with_embeddings': chunks_with_embeddings,
                'embedding_coverage': round((chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0, 1),
                'batch_size': self.batch_size,
                'similarity_threshold': self.similarity_threshold,
                'max_chunks': self.max_chunks
            }
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {str(e)}")
            return {'error': str(e)}
    
    def optimize_embeddings(self) -> Dict[str, Any]:
        """Optimize embeddings by ensuring all active chunks have embeddings."""
        try:
            # Find chunks without embeddings
            chunks_without_embeddings = DocumentChunk.objects.filter(
                is_active=True,
                embedding__isnull=True
            ).exclude(embedding='')
            
            total_chunks = chunks_without_embeddings.count()
            processed = 0
            errors = 0
            
            logger.info(f"Found {total_chunks} chunks without embeddings")
            
            # Process in batches
            for i in range(0, total_chunks, self.batch_size):
                batch = chunks_without_embeddings[i:i + self.batch_size]
                
                for chunk in batch:
                    try:
                        # Generate embedding
                        embedding = self.embedding_service.create_embedding(chunk.content)
                        if embedding:
                            chunk.set_embedding_vector(embedding)
                            chunk.save()
                            processed += 1
                        else:
                            errors += 1
                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk.chunk_id}: {str(e)}")
                        errors += 1
                
                # Log progress
                if (i + self.batch_size) % 50 == 0:
                    logger.info(f"Processed {i + self.batch_size}/{total_chunks} chunks")
            
            return {
                'total_chunks': total_chunks,
                'processed': processed,
                'errors': errors,
                'success_rate': round((processed / total_chunks * 100) if total_chunks > 0 else 0, 1)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing embeddings: {str(e)}")
            return {'error': str(e)}
