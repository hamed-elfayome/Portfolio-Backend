from django.db import models
from django.utils import timezone
from visitors.models import VisitorSession
from projects.models import Project
import uuid

class Conversation(models.Model):
    CONTEXT_TYPES = [
        ('general', 'General Experience'),
        ('project', 'Project Specific'),
        ('skills', 'Skills Discussion'),
        ('job', 'Job Related'),
    ]

    conversation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    visitor_session = models.ForeignKey(VisitorSession, on_delete=models.CASCADE, related_name='conversations')
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name='conversations')
    context_type = models.CharField(max_length=20, choices=CONTEXT_TYPES, default='general')
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    message_count = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_chat_conversation'
        ordering = ['-updated_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        return f"Conversation {self.conversation_id} - {self.get_context_type_display()}"

    def get_message_count(self):
        return self.messages.count()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

class Message(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('assistant', 'AI Response'),
        ('system', 'System Message'),
    ]

    message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='user')
    is_user = models.BooleanField(default=True)  # For backward compatibility
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence score (0-1)")
    context_chunks_used = models.JSONField(default=list, help_text="Document chunks used for context")
    feedback_score = models.IntegerField(null=True, blank=True, help_text="User feedback score (-1, 0, 1)")
    feedback_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_message'
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"Message {self.message_id} - {self.get_message_type_display()}"

    def save(self, *args, **kwargs):
        # Update is_user field based on message_type for backward compatibility
        self.is_user = self.message_type == 'user'
        super().save(*args, **kwargs)

class ChatSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    visitor_session = models.OneToOneField(VisitorSession, on_delete=models.CASCADE, related_name='chat_session')
    current_conversation = models.ForeignKey(Conversation, null=True, blank=True, on_delete=models.SET_NULL)
    total_messages = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_chat_session'
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def __str__(self):
        return f"Chat Session {self.session_id}"

    def get_conversation_history(self):
        return self.visitor_session.conversations.all().order_by('-created_at')
