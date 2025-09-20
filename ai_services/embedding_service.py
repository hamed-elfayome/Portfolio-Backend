"""
Fixed OpenAI Embedding Service using direct API calls.
"""

import requests
import tiktoken
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
import hashlib
import time
import re
import json

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for creating and managing OpenAI embeddings with caching."""
    
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
            logger.warning("OpenAI API key not configured. Embedding service will not work.")
        
        self.model = "text-embedding-ada-002"
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 8192
        self.chunk_size = 500
        self.chunk_overlap = 50
        
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding using direct OpenAI API with caching."""
        try:
            if not self.api_key or not self.headers:
                raise ValueError("OpenAI API key not initialized. Please configure OPENAI_API_KEY.")
            
            # Check cache first
            cache_key = self._get_cache_key(text)
            cached_embedding = self._get_cached_embedding(cache_key)
            if cached_embedding:
                logger.debug(f"Using cached embedding for text: {text[:50]}...")
                return cached_embedding
            
            # Clean and validate text
            text = self._clean_text(text)
            if not text.strip():
                raise ValueError("Empty text provided for embedding")
            
            # Create embedding using direct API
            data = {
                "model": self.model,
                "input": text
            }
            
            response = requests.post(
                'https://api.openai.com/v1/embeddings',
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            embedding = result['data'][0]['embedding']
            
            # Cache the embedding
            self._cache_embedding(cache_key, embedding)
            
            logger.debug(f"Created embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for embedding."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Truncate if too long
        tokens = self.encoding.encode(text)
        if len(tokens) > self.max_tokens:
            text = self.encoding.decode(tokens[:self.max_tokens])
            logger.warning(f"Text truncated to {self.max_tokens} tokens")
        
        return text
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_cached_embedding(self, cache_key: str) -> Optional[List[float]]:
        """Get cached embedding if available."""
        try:
            cached = cache.get(f"embedding_{cache_key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Error getting cached embedding: {e}")
        return None
    
    def _cache_embedding(self, cache_key: str, embedding: List[float]) -> None:
        """Cache embedding for future use."""
        try:
            cache.set(f"embedding_{cache_key}", json.dumps(embedding), timeout=3600*24*7)  # 7 days
        except Exception as e:
            logger.warning(f"Error caching embedding: {e}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for processing."""
        if not text:
            return []
        
        # Clean text first
        text = self._clean_text(text)
        
        # Tokenize
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(tokens):
                break
        
        return chunks
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            try:
                embedding = self.create_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error creating embedding for text: {e}")
                embeddings.append([])  # Empty embedding for failed texts
        
        return embeddings
