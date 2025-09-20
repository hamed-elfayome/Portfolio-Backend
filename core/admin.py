from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'location', 'is_active', 'created_at', 'experience_years_display']
    list_filter = ['is_active', 'created_at', 'location']
    search_fields = ['name', 'email', 'bio', 'location']
    readonly_fields = ['profile_id', 'created_at', 'updated_at', 'skills_display', 'experience_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('profile_id', 'name', 'bio', 'email', 'phone', 'location')
        }),
        ('Online Presence', {
            'fields': ('website', 'linkedin', 'github'),
            'classes': ('collapse',)
        }),
        ('Professional Data', {
            'fields': ('skills', 'skills_display', 'experience', 'experience_display', 'education', 'certifications'),
            'description': 'JSON fields for structured data'
        }),
        ('AI Configuration', {
            'fields': ('ai_personality_prompt',),
            'classes': ('collapse',)
        }),
        ('Resume Management', {
            'fields': ('resume_versions',),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def experience_years_display(self, obj):
        """Display total years of experience."""
        years = obj.get_experience_years()
        return f"{years} years" if years > 0 else "No experience data"
    experience_years_display.short_description = "Experience"
    
    def skills_display(self, obj):
        """Display skills in a readable format."""
        if not obj.skills:
            return "No skills defined"
        
        skills_list = []
        for skill in obj.skills:
            if isinstance(skill, dict):
                name = skill.get('name', 'Unknown')
                level = skill.get('level', '')
                years = skill.get('years', 0)
                skill_text = f"{name}"
                if level:
                    skill_text += f" ({level})"
                if years:
                    skill_text += f" - {years}y"
                skills_list.append(skill_text)
            else:
                skills_list.append(str(skill))
        
        return format_html('<br>'.join(skills_list))
    skills_display.short_description = "Skills"
    
    def experience_display(self, obj):
        """Display experience in a readable format."""
        if not obj.experience:
            return "No experience data"
        
        exp_list = []
        for exp in obj.experience:
            if isinstance(exp, dict):
                title = exp.get('title', 'Unknown Position')
                company = exp.get('company', 'Unknown Company')
                duration = exp.get('duration_years', 0)
                exp_text = f"{title} at {company}"
                if duration:
                    exp_text += f" ({duration}y)"
                exp_list.append(exp_text)
            else:
                exp_list.append(str(exp))
        
        return format_html('<br>'.join(exp_list))
    experience_display.short_description = "Experience"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related()
    
    actions = ['activate_profiles', 'deactivate_profiles']
    
    def activate_profiles(self, request, queryset):
        """Activate selected profiles."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} profiles were successfully activated.")
    activate_profiles.short_description = "Activate selected profiles"
    
    def deactivate_profiles(self, request, queryset):
        """Deactivate selected profiles."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} profiles were successfully deactivated.")
    deactivate_profiles.short_description = "Deactivate selected profiles"
