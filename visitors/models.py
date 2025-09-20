from django.db import models
from django.utils import timezone
import uuid

class VisitorSession(models.Model):
    DEVICE_CHOICES = [
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ]

    BROWSER_CHOICES = [
        ('chrome', 'Chrome'),
        ('firefox', 'Firefox'),
        ('safari', 'Safari'),
        ('edge', 'Edge'),
        ('unknown', 'Unknown'),
    ]

    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session_key = models.CharField(max_length=50, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES, default='desktop')
    browser = models.CharField(max_length=20, choices=BROWSER_CHOICES, default='unknown')
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    page_views_count = models.PositiveIntegerField(default=0)
    time_spent = models.DurationField(null=True, blank=True)
    is_bot = models.BooleanField(default=False)
    is_recruiter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visitors_session'
        ordering = ['-created_at']
        verbose_name = 'Visitor Session'
        verbose_name_plural = 'Visitor Sessions'

    def __str__(self):
        return f"Session {self.session_key[:8]}... ({self.ip_address})"

    def get_session_duration(self):
        if self.time_spent:
            return self.time_spent
        return timezone.now() - self.created_at

class PageView(models.Model):
    page_view_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    visitor_session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='page_views')
    page_url = models.URLField()
    page_title = models.CharField(max_length=200, blank=True)
    referrer = models.URLField(blank=True)
    time_on_page = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'visitors_pageview'
        ordering = ['-created_at']
        verbose_name = 'Page View'
        verbose_name_plural = 'Page Views'

    def __str__(self):
        return f"{self.visitor_session.session_key[:8]}... - {self.page_title}"

class VisitorInteraction(models.Model):
    INTERACTION_TYPES = [
        ('chat_start', 'Chat Started'),
        ('chat_message', 'Chat Message'),
        ('job_analysis', 'Job Analysis'),
        ('project_view', 'Project View'),
        ('download', 'Download'),
        ('contact', 'Contact'),
    ]

    interaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    visitor_session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    details = models.JSONField(default=dict, help_text="Additional interaction details")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'visitors_interaction'
        ordering = ['-created_at']
        verbose_name = 'Visitor Interaction'
        verbose_name_plural = 'Visitor Interactions'

    def __str__(self):
        return f"{self.visitor_session.session_key[:8]}... - {self.get_interaction_type_display()}"
