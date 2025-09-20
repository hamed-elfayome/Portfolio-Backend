from django.db import models
from django.utils import timezone
import uuid

# Note: pgvector import will be added when PostgreSQL is configured
# from pgvector.django import VectorField

class DocumentChunk(models.Model):
    SOURCE_TYPES = [
        ('profile', 'Profile Information'),
        ('project', 'Project Description'),
        ('experience', 'Work Experience'),
        ('skills', 'Skills Information'),
        ('education', 'Education Background'),
        ('resume', 'Resume Content'),
        ('blog', 'Blog Post'),
        ('code', 'Code Documentation'),
    ]

    chunk_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    content = models.TextField()
    # embedding = VectorField(dimensions=1536)  # Will be enabled with pgvector
    embedding = models.TextField(blank=True, help_text="JSON string of embedding vector (temporary until pgvector)")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    source_id = models.CharField(max_length=100, help_text="ID of the source document/object")
    source_title = models.CharField(max_length=200, blank=True)
    chunk_index = models.PositiveIntegerField(default=0)
    token_count = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, help_text="Additional metadata about the chunk")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_services_documentchunk'
        ordering = ['source_type', 'source_id', 'chunk_index']
        verbose_name = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'
        indexes = [
            models.Index(fields=['source_type']),
            models.Index(fields=['source_id']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_source_type_display()} - {self.source_title} (Chunk {self.chunk_index})"

    def get_embedding_vector(self):
        """Get embedding as a list of floats."""
        if self.embedding:
            import json
            try:
                return json.loads(self.embedding)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_embedding_vector(self, vector):
        """Set embedding from a list of floats."""
        import json
        self.embedding = json.dumps(vector)

class EmbeddingCache(models.Model):
    cache_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    text_hash = models.CharField(max_length=64, unique=True, help_text="SHA256 hash of the text")
    text_content = models.TextField()
    # embedding = VectorField(dimensions=1536)  # Will be enabled with pgvector
    embedding = models.TextField(help_text="JSON string of embedding vector (temporary until pgvector)")
    model_name = models.CharField(max_length=50, default="text-embedding-ada-002")
    token_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ai_services_embeddingcache'
        ordering = ['-created_at']
        verbose_name = 'Embedding Cache'
        verbose_name_plural = 'Embedding Caches'

    def __str__(self):
        return f"Embedding Cache: {self.text_hash[:16]}..."

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_embedding_vector(self):
        """Get embedding as a list of floats."""
        if self.embedding:
            import json
            try:
                return json.loads(self.embedding)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_embedding_vector(self, vector):
        """Set embedding from a list of floats."""
        import json
        self.embedding = json.dumps(vector)

class RAGQuery(models.Model):
    query_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    query_text = models.TextField()
    context_type = models.CharField(max_length=20, choices=DocumentChunk.SOURCE_TYPES, blank=True)
    source_id = models.CharField(max_length=100, blank=True)
    chunks_retrieved = models.JSONField(default=list, help_text="IDs of chunks retrieved")
    chunks_used = models.JSONField(default=list, help_text="IDs of chunks actually used")
    similarity_scores = models.JSONField(default=list, help_text="Similarity scores for retrieved chunks")
    response_generated = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_services_ragquery'
        ordering = ['-created_at']
        verbose_name = 'RAG Query'
        verbose_name_plural = 'RAG Queries'

    def __str__(self):
        return f"RAG Query: {self.query_text[:50]}..."

class ContentProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    job_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    source_type = models.CharField(max_length=20, choices=DocumentChunk.SOURCE_TYPES)
    source_id = models.CharField(max_length=100)
    source_title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    chunks_created = models.PositiveIntegerField(default=0)
    embeddings_generated = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_services_contentprocessingjob'
        ordering = ['-created_at']
        verbose_name = 'Content Processing Job'
        verbose_name_plural = 'Content Processing Jobs'

    def __str__(self):
        return f"Processing Job: {self.get_source_type_display()} - {self.source_title}"
