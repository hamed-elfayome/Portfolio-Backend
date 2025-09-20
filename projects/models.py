from django.db import models
from django.utils.text import slugify
from core.models import Profile
import uuid

class Project(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('archived', 'Archived'),
    ]

    project_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)
    tech_stack = models.JSONField(default=list, help_text="Technologies used in the project")
    github_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_open_source = models.BooleanField(default=False)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    complexity_score = models.FloatField(null=True, blank=True, help_text="1-10 complexity rating")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    team_size = models.PositiveIntegerField(default=1)
    my_role = models.CharField(max_length=100, blank=True)
    achievements = models.JSONField(default=list, help_text="Project achievements and outcomes")
    challenges = models.JSONField(default=list, help_text="Challenges faced and solutions")
    learnings = models.TextField(blank=True, help_text="Key learnings from the project")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_project'
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        indexes = [
            models.Index(fields=['is_featured']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_tech_stack_list(self):
        return [tech.get('name', str(tech)) for tech in self.tech_stack if tech]

    def get_duration_months(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days // 30
        return None

    def get_primary_image(self):
        return self.images.filter(is_primary=True).first()

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        db_table = 'projects_image'

    def __str__(self):
        return f"{self.project.title} - Image {self.order}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per project
            ProjectImage.objects.filter(project=self.project, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
