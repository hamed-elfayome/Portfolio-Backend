from django.contrib import admin
from django.utils.html import format_html
from .models import JobAnalysis, SkillsMatch, JobRecommendation

class SkillsMatchInline(admin.TabularInline):
    model = SkillsMatch
    extra = 0
    fields = ['job_skill', 'profile_skill', 'match_type', 'confidence_score', 'is_required', 'years_experience']
    readonly_fields = ['match_id']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-confidence_score', 'job_skill')

class JobRecommendationInline(admin.TabularInline):
    model = JobRecommendation
    extra = 0
    fields = ['recommendation_type', 'title', 'priority', 'estimated_time']
    readonly_fields = ['recommendation_id']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('priority', 'created_at')

@admin.register(JobAnalysis)
class JobAnalysisAdmin(admin.ModelAdmin):
    list_display = ['analysis_id_short', 'job_title', 'company_name', 'overall_match_score', 'match_level_display', 'visitor_session_short', 'created_at']
    list_filter = ['created_at', 'overall_match_score']
    search_fields = ['job_title', 'company_name', 'job_requirements', 'visitor_session__session_key']
    readonly_fields = ['analysis_id', 'processing_time', 'tokens_used', 'created_at', 'match_level_display', 'scores_display']
    inlines = [SkillsMatchInline, JobRecommendationInline]
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis_id', 'visitor_session', 'job_title', 'company_name', 'job_requirements', 'uploaded_file', 'file_processed')
        }),
        ('Match Scores', {
            'fields': ('overall_match_score', 'skills_match_score', 'experience_match_score', 'education_match_score', 'scores_display', 'match_level_display')
        }),
        ('Analysis Results', {
            'fields': ('matched_skills', 'missing_skills', 'skill_gaps', 'experience_analysis', 'education_analysis', 'recommendations_data'),
            'classes': ('collapse',)
        }),
        ('Processing Information', {
            'fields': ('processing_time', 'tokens_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def analysis_id_short(self, obj):
        """Display shortened analysis ID."""
        return f"{str(obj.analysis_id)[:8]}..."
    analysis_id_short.short_description = "Analysis ID"
    
    def visitor_session_short(self, obj):
        """Display shortened session key."""
        return f"{obj.visitor_session.session_key[:12]}..."
    visitor_session_short.short_description = "Session"
    
    def match_level_display(self, obj):
        """Display match level with color coding."""
        level = obj.get_match_level()
        colors = {
            'excellent': 'green',
            'good': 'blue',
            'fair': 'orange',
            'poor': 'red'
        }
        color = colors.get(level, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_match_level_display()
        )
    match_level_display.short_description = "Match Level"
    
    def scores_display(self, obj):
        """Display all scores in a readable format."""
        return format_html(
            '<strong>Overall:</strong> {}%<br>'
            '<strong>Skills:</strong> {}%<br>'
            '<strong>Experience:</strong> {}%<br>'
            '<strong>Education:</strong> {}%',
            obj.overall_match_score,
            obj.skills_match_score,
            obj.experience_match_score,
            obj.education_match_score
        )
    scores_display.short_description = "All Scores"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('visitor_session').prefetch_related('skills_matches', 'recommendations')
    
    actions = ['recalculate_scores']
    
    def recalculate_scores(self, request, queryset):
        """Recalculate match scores for selected analyses."""
        # This would trigger a recalculation - placeholder for now
        self.message_user(request, f"Score recalculation triggered for {queryset.count()} analyses.")
    recalculate_scores.short_description = "Recalculate scores"

@admin.register(SkillsMatch)
class SkillsMatchAdmin(admin.ModelAdmin):
    list_display = ['match_id_short', 'job_analysis_short', 'job_skill', 'profile_skill', 'match_type', 'confidence_score', 'is_required', 'years_experience']
    list_filter = ['match_type', 'is_required', 'confidence_score']
    search_fields = ['job_skill', 'profile_skill', 'job_analysis__job_title']
    readonly_fields = ['match_id']
    
    fieldsets = (
        ('Match Information', {
            'fields': ('match_id', 'job_analysis', 'job_skill', 'profile_skill', 'match_type')
        }),
        ('Match Details', {
            'fields': ('confidence_score', 'is_required', 'years_experience', 'proficiency_level')
        }),
    )
    
    def match_id_short(self, obj):
        """Display shortened match ID."""
        return f"{str(obj.match_id)[:8]}..."
    match_id_short.short_description = "Match ID"
    
    def job_analysis_short(self, obj):
        """Display shortened job analysis info."""
        return f"{obj.job_analysis.job_title[:30]}..." if len(obj.job_analysis.job_title) > 30 else obj.job_analysis.job_title
    job_analysis_short.short_description = "Job Analysis"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('job_analysis')

@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ['recommendation_id_short', 'job_analysis_short', 'recommendation_type', 'title', 'priority', 'estimated_time', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'created_at']
    search_fields = ['title', 'description', 'job_analysis__job_title']
    readonly_fields = ['recommendation_id', 'created_at']
    
    fieldsets = (
        ('Recommendation Information', {
            'fields': ('recommendation_id', 'job_analysis', 'recommendation_type', 'title', 'description', 'priority')
        }),
        ('Implementation Details', {
            'fields': ('estimated_time', 'resources', 'skills_involved'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def recommendation_id_short(self, obj):
        """Display shortened recommendation ID."""
        return f"{str(obj.recommendation_id)[:8]}..."
    recommendation_id_short.short_description = "Recommendation ID"
    
    def job_analysis_short(self, obj):
        """Display shortened job analysis info."""
        return f"{obj.job_analysis.job_title[:30]}..." if len(obj.job_analysis.job_title) > 30 else obj.job_analysis.job_title
    job_analysis_short.short_description = "Job Analysis"
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related('job_analysis')
