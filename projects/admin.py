from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Project, ProjectImage

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'order']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('order', 'created_at')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'profile', 'status', 'difficulty_level', 'is_featured', 'complexity_score', 'created_at']
    list_filter = ['status', 'difficulty_level', 'is_featured', 'is_open_source', 'created_at']
    search_fields = ['title', 'description', 'profile__name', 'tech_stack']
    readonly_fields = ['project_id', 'slug', 'created_at', 'updated_at', 'tech_stack_display', 'duration_display']
    inlines = [ProjectImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_id', 'profile', 'title', 'slug', 'description', 'detailed_description')
        }),
        ('Project Details', {
            'fields': ('status', 'difficulty_level', 'complexity_score', 'is_featured', 'is_open_source')
        }),
        ('Timeline & Team', {
            'fields': ('start_date', 'end_date', 'duration_display', 'team_size', 'my_role'),
            'classes': ('collapse',)
        }),
        ('Technology & Links', {
            'fields': ('tech_stack', 'tech_stack_display', 'github_url', 'demo_url', 'documentation_url')
        }),
        ('Project Insights', {
            'fields': ('achievements', 'challenges', 'learnings'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tech_stack_display(self, obj):
        """Display tech stack in a readable format."""
        if not obj.tech_stack:
            return "No technologies specified"
        
        tech_list = []
        for tech in obj.tech_stack:
            if isinstance(tech, dict):
                name = tech.get('name', 'Unknown')
                category = tech.get('category', '')
                tech_text = name
                if category:
                    tech_text += f" ({category})"
                tech_list.append(tech_text)
            else:
                tech_list.append(str(tech))
        
        return format_html('<br>'.join(tech_list))
    tech_stack_display.short_description = "Technologies"
    
    def duration_display(self, obj):
        """Display project duration."""
        months = obj.get_duration_months()
        if months:
            if months >= 12:
                years = months // 12
                remaining_months = months % 12
                if remaining_months > 0:
                    return f"{years}y {remaining_months}m"
                return f"{years}y"
            return f"{months}m"
        return "Duration not specified"
    duration_display.short_description = "Duration"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('profile').prefetch_related('images')
    
    actions = ['mark_featured', 'mark_completed', 'mark_archived']
    
    def mark_featured(self, request, queryset):
        """Mark selected projects as featured."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} projects were marked as featured.")
    mark_featured.short_description = "Mark as featured"
    
    def mark_completed(self, request, queryset):
        """Mark selected projects as completed."""
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} projects were marked as completed.")
    mark_completed.short_description = "Mark as completed"
    
    def mark_archived(self, request, queryset):
        """Mark selected projects as archived."""
        updated = queryset.update(status='archived')
        self.message_user(request, f"{updated} projects were marked as archived.")
    mark_archived.short_description = "Mark as archived"

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['project', 'caption', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['project__title', 'caption']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Image Information', {
            'fields': ('project', 'image', 'caption', 'is_primary', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('project')
