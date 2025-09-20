from django.db import models
from django.utils import timezone
from visitors.models import VisitorSession
import uuid

class JobAnalysis(models.Model):
    MATCH_LEVELS = [
        ('excellent', 'Excellent Match (90-100%)'),
        ('good', 'Good Match (70-89%)'),
        ('fair', 'Fair Match (50-69%)'),
        ('poor', 'Poor Match (0-49%)'),
    ]

    analysis_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    visitor_session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='job_analyses')
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    job_requirements = models.TextField()
    uploaded_file = models.FileField(upload_to='job_docs/', null=True, blank=True)
    file_processed = models.BooleanField(default=False)
    
    # Match Scores (0-100)
    overall_match_score = models.FloatField(help_text="Overall match percentage")
    skills_match_score = models.FloatField(help_text="Skills match percentage")
    experience_match_score = models.FloatField(help_text="Experience match percentage")
    education_match_score = models.FloatField(help_text="Education match percentage")
    
    # Analysis Results
    matched_skills = models.JSONField(default=list, help_text="Skills that match job requirements")
    missing_skills = models.JSONField(default=list, help_text="Required skills not found in profile")
    skill_gaps = models.JSONField(default=list, help_text="Skills that need improvement")
    experience_analysis = models.JSONField(default=dict, help_text="Experience comparison analysis")
    education_analysis = models.JSONField(default=dict, help_text="Education comparison analysis")
    recommendations_data = models.JSONField(default=list, help_text="Actionable recommendations")
    
    # Metadata
    processing_time = models.FloatField(help_text="Analysis processing time in seconds")
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_matching_analysis'
        ordering = ['-created_at']
        verbose_name = 'Job Analysis'
        verbose_name_plural = 'Job Analyses'

    def __str__(self):
        return f"Job Analysis: {self.job_title} at {self.company_name}"

    def get_match_level(self):
        """Get match level based on overall score."""
        if self.overall_match_score >= 90:
            return 'excellent'
        elif self.overall_match_score >= 70:
            return 'good'
        elif self.overall_match_score >= 50:
            return 'fair'
        else:
            return 'poor'

    def get_match_level_display(self):
        """Get human-readable match level."""
        level = self.get_match_level()
        for choice in self.MATCH_LEVELS:
            if choice[0] == level:
                return choice[1]
        return 'Unknown'

class SkillsMatch(models.Model):
    match_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    job_analysis = models.ForeignKey(JobAnalysis, on_delete=models.CASCADE, related_name='skills_matches')
    job_skill = models.CharField(max_length=100)
    profile_skill = models.CharField(max_length=100)
    match_type = models.CharField(max_length=20, choices=[
        ('exact', 'Exact Match'),
        ('similar', 'Similar Match'),
        ('related', 'Related Match'),
    ])
    confidence_score = models.FloatField(help_text="Match confidence (0-1)")
    is_required = models.BooleanField(default=False)
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    proficiency_level = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'job_matching_skillsmatch'
        verbose_name = 'Skills Match'
        verbose_name_plural = 'Skills Matches'

    def __str__(self):
        return f"{self.job_skill} -> {self.profile_skill} ({self.get_match_type_display()})"

class JobRecommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('skill', 'Skill Development'),
        ('experience', 'Experience Building'),
        ('education', 'Education'),
        ('project', 'Project Work'),
        ('certification', 'Certification'),
    ]

    PRIORITY_LEVELS = [
        ('high', 'High Priority'),
        ('medium', 'Medium Priority'),
        ('low', 'Low Priority'),
    ]

    recommendation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    job_analysis = models.ForeignKey(JobAnalysis, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    estimated_time = models.CharField(max_length=50, blank=True, help_text="Estimated time to complete")
    resources = models.JSONField(default=list, help_text="Helpful resources or links")
    skills_involved = models.JSONField(default=list, help_text="Skills this recommendation addresses")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_matching_recommendation'
        ordering = ['priority', 'created_at']
        verbose_name = 'Job Recommendation'
        verbose_name_plural = 'Job Recommendations'

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
