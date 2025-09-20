from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, Message, ChatSession

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ['message_type', 'content_short', 'response_time', 'confidence_score', 'created_at']
    readonly_fields = ['message_id', 'created_at', 'content_short']
    
    def content_short(self, obj):
        """Display shortened message content."""
        if len(obj.content) > 100:
            return f"{obj.content[:97]}..."
        return obj.content
    content_short.short_description = "Content"
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('created_at')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id_short', 'visitor_session_short', 'context_type', 'project', 'is_active', 'message_count', 'total_tokens_used', 'created_at']
    list_filter = ['context_type', 'is_active', 'created_at']
    search_fields = ['title', 'visitor_session__session_key', 'project__title']
    readonly_fields = ['conversation_id', 'message_count', 'total_tokens_used', 'created_at', 'updated_at']
    inlines = [MessageInline]
    
    fieldsets = (
        ('Conversation Information', {
            'fields': ('conversation_id', 'visitor_session', 'project', 'context_type', 'title', 'is_active')
        }),
        ('Statistics', {
            'fields': ('message_count', 'total_tokens_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def conversation_id_short(self, obj):
        """Display shortened conversation ID."""
        return f"{str(obj.conversation_id)[:8]}..."
    conversation_id_short.short_description = "Conversation ID"
    
    def visitor_session_short(self, obj):
        """Display shortened session key."""
        return f"{obj.visitor_session.session_key[:12]}..."
    visitor_session_short.short_description = "Session"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('visitor_session', 'project').prefetch_related('messages')
    
    actions = ['activate_conversations', 'deactivate_conversations']
    
    def activate_conversations(self, request, queryset):
        """Activate selected conversations."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} conversations were activated.")
    activate_conversations.short_description = "Activate conversations"
    
    def deactivate_conversations(self, request, queryset):
        """Deactivate selected conversations."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} conversations were deactivated.")
    deactivate_conversations.short_description = "Deactivate conversations"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['message_id_short', 'conversation_short', 'message_type', 'content_short', 'response_time', 'confidence_score', 'created_at']
    list_filter = ['message_type', 'created_at']
    search_fields = ['content', 'conversation__title', 'conversation__visitor_session__session_key']
    readonly_fields = ['message_id', 'created_at']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'conversation', 'message_type', 'content')
        }),
        ('AI Metrics', {
            'fields': ('response_time', 'tokens_used', 'confidence_score', 'context_chunks_used'),
            'classes': ('collapse',)
        }),
        ('User Feedback', {
            'fields': ('feedback_score', 'feedback_comment'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def message_id_short(self, obj):
        """Display shortened message ID."""
        return f"{str(obj.message_id)[:8]}..."
    message_id_short.short_description = "Message ID"
    
    def conversation_short(self, obj):
        """Display shortened conversation info."""
        return f"{str(obj.conversation.conversation_id)[:8]}... ({obj.conversation.get_context_type_display()})"
    conversation_short.short_description = "Conversation"
    
    def content_short(self, obj):
        """Display shortened message content."""
        if len(obj.content) > 80:
            return f"{obj.content[:77]}..."
        return obj.content
    content_short.short_description = "Content"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('conversation__visitor_session', 'conversation__project')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id_short', 'visitor_session_short', 'current_conversation_short', 'total_messages', 'total_tokens_used', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['visitor_session__session_key']
    readonly_fields = ['session_id', 'total_messages', 'total_tokens_used', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'visitor_session', 'current_conversation', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_messages', 'total_tokens_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def session_id_short(self, obj):
        """Display shortened session ID."""
        return f"{str(obj.session_id)[:8]}..."
    session_id_short.short_description = "Session ID"
    
    def visitor_session_short(self, obj):
        """Display shortened session key."""
        return f"{obj.visitor_session.session_key[:12]}..."
    visitor_session_short.short_description = "Visitor Session"
    
    def current_conversation_short(self, obj):
        """Display shortened current conversation info."""
        if obj.current_conversation:
            return f"{str(obj.current_conversation.conversation_id)[:8]}... ({obj.current_conversation.get_context_type_display()})"
        return "No active conversation"
    current_conversation_short.short_description = "Current Conversation"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('visitor_session', 'current_conversation')
