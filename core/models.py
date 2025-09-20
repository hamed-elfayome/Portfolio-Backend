from django.db import models
from django.core.validators import EmailValidator
import uuid

class Profile(models.Model):
    profile_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100)
    bio = models.TextField()
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    skills = models.JSONField(default=list, help_text="List of skills with proficiency levels")
    experience = models.JSONField(default=list, help_text="Work experience data")
    education = models.JSONField(default=list, help_text="Education background")
    certifications = models.JSONField(default=list, help_text="Professional certifications")
    resume_versions = models.JSONField(default=dict, help_text="Different resume versions")
    ai_personality_prompt = models.TextField(
        help_text="Prompt that defines AI personality for responses",
        default="You are a helpful AI assistant representing this developer's portfolio."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_profile'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.name

    def get_skills_list(self):
        return [skill.get('name', '') for skill in self.skills if isinstance(skill, dict)]

    def get_experience_years(self):
        total_years = 0
        for exp in self.experience:
            if isinstance(exp, dict) and 'duration_years' in exp:
                total_years += exp['duration_years']
        return total_years

    def get_primary_skills(self, limit=10):
        """Get top skills by proficiency or years of experience."""
        skills = [s for s in self.skills if isinstance(s, dict)]
        return sorted(skills, key=lambda x: x.get('years', 0), reverse=True)[:limit]
