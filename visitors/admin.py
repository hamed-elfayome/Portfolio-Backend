from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import VisitorSession, PageView, VisitorInteraction

class PageViewInline(admin.TabularInline):
    model = PageView
    extra = 0
    fields = ['page_url', 'page_title', 'time_on_page', 'created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')

class VisitorInteractionInline(admin.TabularInline):
    model = VisitorInteraction
    extra = 0
    fields = ['interaction_type', 'details', 'created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')

@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ['session_key_short', 'ip_address', 'device_type', 'browser', 'page_views_count', 'is_bot', 'is_recruiter', 'created_at']
    list_filter = ['device_type', 'browser', 'is_bot', 'is_recruiter', 'created_at']
    search_fields = ['session_key', 'ip_address', 'user_agent', 'country', 'city']
    readonly_fields = ['session_id', 'session_key', 'created_at', 'last_activity', 'session_duration_display']
    inlines = [PageViewInline, VisitorInteractionInline]
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'session_key', 'ip_address', 'user_agent')
        }),
        ('Device & Location', {
            'fields': ('device_type', 'browser', 'country', 'city'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('page_views_count', 'time_spent', 'session_duration_display', 'is_bot', 'is_recruiter')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def session_key_short(self, obj):
        """Display shortened session key."""
        return f"{obj.session_key[:12]}..."
    session_key_short.short_description = "Session Key"
    
    def session_duration_display(self, obj):
        """Display session duration."""
        duration = obj.get_session_duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "Unknown"
    session_duration_display.short_description = "Duration"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).prefetch_related('page_views', 'interactions')
    
    actions = ['mark_as_recruiter', 'mark_as_bot', 'clear_analytics']
    
    def mark_as_recruiter(self, request, queryset):
        """Mark selected sessions as recruiter visits."""
        updated = queryset.update(is_recruiter=True)
        self.message_user(request, f"{updated} sessions were marked as recruiter visits.")
    mark_as_recruiter.short_description = "Mark as recruiter"
    
    def mark_as_bot(self, request, queryset):
        """Mark selected sessions as bot visits."""
        updated = queryset.update(is_bot=True)
        self.message_user(request, f"{updated} sessions were marked as bot visits.")
    mark_as_bot.short_description = "Mark as bot"
    
    def clear_analytics(self, request, queryset):
        """Clear analytics data for selected sessions."""
        for session in queryset:
            session.page_views.all().delete()
            session.interactions.all().delete()
            session.page_views_count = 0
            session.time_spent = None
            session.save()
        self.message_user(request, f"Analytics data cleared for {queryset.count()} sessions.")
    clear_analytics.short_description = "Clear analytics data"

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['visitor_session_short', 'page_title', 'page_url_short', 'time_on_page', 'created_at']
    list_filter = ['created_at']
    search_fields = ['page_url', 'page_title', 'visitor_session__session_key']
    readonly_fields = ['page_view_id', 'created_at']
    
    fieldsets = (
        ('Page View Information', {
            'fields': ('page_view_id', 'visitor_session', 'page_url', 'page_title', 'referrer')
        }),
        ('Analytics', {
            'fields': ('time_on_page',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def visitor_session_short(self, obj):
        """Display shortened session key."""
        return f"{obj.visitor_session.session_key[:12]}..."
    visitor_session_short.short_description = "Session"
    
    def page_url_short(self, obj):
        """Display shortened page URL."""
        if len(obj.page_url) > 50:
            return f"{obj.page_url[:47]}..."
        return obj.page_url
    page_url_short.short_description = "Page URL"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('visitor_session')

@admin.register(VisitorInteraction)
class VisitorInteractionAdmin(admin.ModelAdmin):
    list_display = ['visitor_session_short', 'interaction_type', 'details_short', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['visitor_session__session_key', 'details']
    readonly_fields = ['interaction_id', 'created_at']
    
    fieldsets = (
        ('Interaction Information', {
            'fields': ('interaction_id', 'visitor_session', 'interaction_type', 'details')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def visitor_session_short(self, obj):
        """Display shortened session key."""
        return f"{obj.visitor_session.session_key[:12]}..."
    visitor_session_short.short_description = "Session"
    
    def details_short(self, obj):
        """Display shortened interaction details."""
        if obj.details:
            details_str = str(obj.details)
            if len(details_str) > 50:
                return f"{details_str[:47]}..."
            return details_str
        return "No details"
    details_short.short_description = "Details"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('visitor_session')
