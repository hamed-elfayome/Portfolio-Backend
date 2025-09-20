from django.contrib import admin
from django.utils.html import format_html
from .models import DocumentChunk, EmbeddingCache, RAGQuery, ContentProcessingJob

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['chunk_id_short', 'source_type', 'source_title', 'chunk_index', 'token_count', 'is_active', 'created_at']
    list_filter = ['source_type', 'is_active', 'created_at']
    search_fields = ['content', 'source_title', 'source_id']
    readonly_fields = ['chunk_id', 'created_at', 'updated_at', 'embedding_info']
    
    fieldsets = (
        ('Chunk Information', {
            'fields': ('chunk_id', 'content', 'source_type', 'source_id', 'source_title', 'chunk_index')
        }),
        ('Embedding Data', {
            'fields': ('embedding', 'embedding_info', 'token_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def chunk_id_short(self, obj):
        """Display shortened chunk ID."""
        return f"{str(obj.chunk_id)[:8]}..."
    chunk_id_short.short_description = "Chunk ID"
    
    def embedding_info(self, obj):
        """Display embedding information."""
        if obj.embedding:
            vector = obj.get_embedding_vector()
            if vector:
                return f"Vector length: {len(vector)}, First 3 values: {vector[:3]}"
            return "Invalid embedding data"
        return "No embedding data"
    embedding_info.short_description = "Embedding Info"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request)
    
    actions = ['activate_chunks', 'deactivate_chunks']
    
    def activate_chunks(self, request, queryset):
        """Activate selected chunks."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} chunks were activated.")
    activate_chunks.short_description = "Activate chunks"
    
    def deactivate_chunks(self, request, queryset):
        """Deactivate selected chunks."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} chunks were deactivated.")
    deactivate_chunks.short_description = "Deactivate chunks"

@admin.register(EmbeddingCache)
class EmbeddingCacheAdmin(admin.ModelAdmin):
    list_display = ['cache_id_short', 'text_hash_short', 'model_name', 'token_count', 'is_expired_display', 'created_at']
    list_filter = ['model_name', 'created_at']
    search_fields = ['text_content', 'text_hash']
    readonly_fields = ['cache_id', 'text_hash', 'created_at', 'embedding_info']
    
    fieldsets = (
        ('Cache Information', {
            'fields': ('cache_id', 'text_hash', 'text_content', 'model_name', 'token_count')
        }),
        ('Embedding Data', {
            'fields': ('embedding', 'embedding_info'),
            'classes': ('collapse',)
        }),
        ('Expiration', {
            'fields': ('expires_at',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def cache_id_short(self, obj):
        """Display shortened cache ID."""
        return f"{str(obj.cache_id)[:8]}..."
    cache_id_short.short_description = "Cache ID"
    
    def text_hash_short(self, obj):
        """Display shortened text hash."""
        return f"{obj.text_hash[:16]}..."
    text_hash_short.short_description = "Text Hash"
    
    def is_expired_display(self, obj):
        """Display expiration status with color coding."""
        is_expired = obj.is_expired()
        color = 'red' if is_expired else 'green'
        status = 'Expired' if is_expired else 'Valid'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_expired_display.short_description = "Status"
    
    def embedding_info(self, obj):
        """Display embedding information."""
        if obj.embedding:
            vector = obj.get_embedding_vector()
            if vector:
                return f"Vector length: {len(vector)}, First 3 values: {vector[:3]}"
            return "Invalid embedding data"
        return "No embedding data"
    embedding_info.short_description = "Embedding Info"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request)
    
    actions = ['clear_expired_cache']
    
    def clear_expired_cache(self, request, queryset):
        """Clear expired cache entries."""
        expired_count = 0
        for cache_entry in queryset:
            if cache_entry.is_expired():
                cache_entry.delete()
                expired_count += 1
        self.message_user(request, f"{expired_count} expired cache entries were cleared.")
    clear_expired_cache.short_description = "Clear expired cache"

@admin.register(RAGQuery)
class RAGQueryAdmin(admin.ModelAdmin):
    list_display = ['query_id_short', 'query_text_short', 'context_type', 'confidence_score', 'processing_time', 'tokens_used', 'created_at']
    list_filter = ['context_type', 'created_at']
    search_fields = ['query_text', 'response_generated']
    readonly_fields = ['query_id', 'created_at', 'chunks_info']
    
    fieldsets = (
        ('Query Information', {
            'fields': ('query_id', 'query_text', 'context_type', 'source_id')
        }),
        ('Retrieval Results', {
            'fields': ('chunks_retrieved', 'chunks_used', 'similarity_scores', 'chunks_info'),
            'classes': ('collapse',)
        }),
        ('Response Generation', {
            'fields': ('response_generated', 'confidence_score'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('tokens_used', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def query_id_short(self, obj):
        """Display shortened query ID."""
        return f"{str(obj.query_id)[:8]}..."
    query_id_short.short_description = "Query ID"
    
    def query_text_short(self, obj):
        """Display shortened query text."""
        if len(obj.query_text) > 50:
            return f"{obj.query_text[:47]}..."
        return obj.query_text
    query_text_short.short_description = "Query Text"
    
    def chunks_info(self, obj):
        """Display chunks information."""
        retrieved = len(obj.chunks_retrieved) if obj.chunks_retrieved else 0
        used = len(obj.chunks_used) if obj.chunks_used else 0
        return f"Retrieved: {retrieved}, Used: {used}"
    chunks_info.short_description = "Chunks Info"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request)

@admin.register(ContentProcessingJob)
class ContentProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['job_id_short', 'source_type', 'source_title', 'status', 'chunks_created', 'embeddings_generated', 'processing_time', 'created_at']
    list_filter = ['status', 'source_type', 'created_at']
    search_fields = ['source_title', 'content', 'error_message']
    readonly_fields = ['job_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('job_id', 'source_type', 'source_id', 'source_title', 'content', 'status')
        }),
        ('Processing Results', {
            'fields': ('chunks_created', 'embeddings_generated', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def job_id_short(self, obj):
        """Display shortened job ID."""
        return f"{str(obj.job_id)[:8]}..."
    job_id_short.short_description = "Job ID"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request)
    
    actions = ['retry_failed_jobs', 'cancel_pending_jobs']
    
    def retry_failed_jobs(self, request, queryset):
        """Retry failed jobs."""
        failed_jobs = queryset.filter(status='failed')
        updated = failed_jobs.update(status='pending', error_message='')
        self.message_user(request, f"{updated} failed jobs were reset to pending.")
    retry_failed_jobs.short_description = "Retry failed jobs"
    
    def cancel_pending_jobs(self, request, queryset):
        """Cancel pending jobs."""
        pending_jobs = queryset.filter(status='pending')
        updated = pending_jobs.update(status='failed', error_message='Cancelled by admin')
        self.message_user(request, f"{updated} pending jobs were cancelled.")
    cancel_pending_jobs.short_description = "Cancel pending jobs"
