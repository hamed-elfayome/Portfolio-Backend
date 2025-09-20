from rest_framework import serializers
from core.models import Profile
from projects.models import Project, ProjectImage
from visitors.models import VisitorSession, PageView, VisitorInteraction
from ai_chat.models import Conversation, Message, ChatSession
from job_matching.models import JobAnalysis, SkillsMatch, JobRecommendation
from ai_services.models import DocumentChunk, EmbeddingCache, RAGQuery, ContentProcessingJob


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model with computed fields."""
    skills_list = serializers.ReadOnlyField(source='get_skills_list')
    experience_years = serializers.ReadOnlyField(source='get_experience_years')
    primary_skills = serializers.ReadOnlyField(source='get_primary_skills')
    
    class Meta:
        model = Profile
        fields = [
            'profile_id', 'name', 'bio', 'email', 'phone', 'location',
            'website', 'linkedin', 'github', 'skills', 'experience',
            'education', 'certifications', 'resume_versions', 
            'ai_personality_prompt', 'is_active', 'skills_list', 
            'experience_years', 'primary_skills', 'created_at', 'updated_at'
        ]
        read_only_fields = ['profile_id', 'created_at', 'updated_at']


class ProjectImageSerializer(serializers.ModelSerializer):
    """Serializer for ProjectImage model."""
    
    class Meta:
        model = ProjectImage
        fields = [
            'image', 'caption', 'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['created_at']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model with related images."""
    images = ProjectImageSerializer(many=True, read_only=True)
    tech_stack_list = serializers.ReadOnlyField(source='get_tech_stack_list')
    duration_months = serializers.ReadOnlyField(source='get_duration_months')
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'project_id', 'profile', 'title', 'slug', 'description', 
            'detailed_description', 'tech_stack', 'tech_stack_list',
            'github_url', 'demo_url', 'documentation_url', 'is_featured',
            'is_open_source', 'difficulty_level', 'status', 'complexity_score',
            'start_date', 'end_date', 'team_size', 'my_role', 'achievements',
            'challenges', 'learnings', 'duration_months', 'images', 
            'primary_image', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['project_id', 'slug', 'created_at', 'updated_at']
    
    def get_primary_image(self, obj):
        """Get the primary image URL for the project."""
        primary_image = obj.get_primary_image()
        if primary_image:
            return primary_image.image.url
        return None


class VisitorSessionSerializer(serializers.ModelSerializer):
    """Serializer for VisitorSession model."""
    session_duration = serializers.ReadOnlyField(source='get_session_duration')
    
    class Meta:
        model = VisitorSession
        fields = [
            'session_id', 'session_key', 'ip_address', 'user_agent',
            'referrer', 'device_type', 'browser', 'is_recruiter',
            'is_bot', 'page_views', 'session_duration', 'created_at',
            'last_activity'
        ]
        read_only_fields = ['session_id', 'created_at', 'last_activity']


class PageViewSerializer(serializers.ModelSerializer):
    """Serializer for PageView model."""
    
    class Meta:
        model = PageView
        fields = [
            'page_view_id', 'visitor_session', 'page_url', 'page_title',
            'time_on_page', 'created_at'
        ]
        read_only_fields = ['page_view_id', 'created_at']


class VisitorInteractionSerializer(serializers.ModelSerializer):
    """Serializer for VisitorInteraction model."""
    
    class Meta:
        model = VisitorInteraction
        fields = [
            'interaction_id', 'visitor_session', 'interaction_type',
            'details', 'created_at'
        ]
        read_only_fields = ['interaction_id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'conversation', 'content', 'is_user',
            'response_time', 'confidence_score', 'tokens_used',
            'feedback_score', 'context_chunks_used', 'created_at'
        ]
        read_only_fields = ['message_id', 'created_at', 'response_time']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model with related messages."""
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.ReadOnlyField(source='get_message_count')
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'visitor_session', 'project', 'context_type',
            'title', 'is_active', 'message_count', 'messages', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession model."""
    
    class Meta:
        model = ChatSession
        fields = [
            'session_id', 'visitor_session', 'current_conversation',
            'total_messages', 'total_questions', 'total_answers',
            'average_response_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['session_id', 'created_at', 'updated_at']


class SkillsMatchSerializer(serializers.ModelSerializer):
    """Serializer for SkillsMatch model."""
    
    class Meta:
        model = SkillsMatch
        fields = [
            'match_id', 'job_analysis', 'skill_name', 'match_type',
            'confidence_score', 'is_required', 'is_preferred',
            'profile_skill', 'years_experience', 'created_at'
        ]
        read_only_fields = ['match_id', 'created_at']


class JobRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for JobRecommendation model."""
    
    class Meta:
        model = JobRecommendation
        fields = [
            'recommendation_id', 'job_analysis', 'recommendation_type',
            'priority', 'title', 'description', 'implementation_details',
            'estimated_effort', 'created_at'
        ]
        read_only_fields = ['recommendation_id', 'created_at']


class JobAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for JobAnalysis model with related data."""
    skills_matches = SkillsMatchSerializer(many=True, read_only=True)
    recommendations = JobRecommendationSerializer(many=True, read_only=True)
    match_level = serializers.ReadOnlyField(source='get_match_level')
    
    class Meta:
        model = JobAnalysis
        fields = [
            'analysis_id', 'visitor_session', 'job_title', 'company_name',
            'job_requirements', 'uploaded_file', 'file_processed',
            'overall_match_score', 'skills_match_score', 'experience_match_score',
            'education_match_score', 'matched_skills', 'missing_skills',
            'skill_gaps', 'experience_analysis', 'education_analysis',
            'recommendations', 'match_level', 'processing_time',
            'skills_matches', 'recommendations', 'created_at'
        ]
        read_only_fields = ['analysis_id', 'processing_time', 'created_at']


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model."""
    
    class Meta:
        model = DocumentChunk
        fields = [
            'chunk_id', 'content', 'embedding', 'source_type', 'source_id',
            'source_title', 'chunk_index', 'token_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['chunk_id', 'created_at', 'updated_at']


class EmbeddingCacheSerializer(serializers.ModelSerializer):
    """Serializer for EmbeddingCache model."""
    
    class Meta:
        model = EmbeddingCache
        fields = [
            'cache_id', 'text_hash', 'embedding', 'model_name',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['cache_id', 'created_at']


class RAGQuerySerializer(serializers.ModelSerializer):
    """Serializer for RAGQuery model."""
    
    class Meta:
        model = RAGQuery
        fields = [
            'query_id', 'query_text', 'context_type', 'source_id',
            'chunks_retrieved', 'chunks_used', 'response_time',
            'confidence_score', 'tokens_used', 'created_at'
        ]
        read_only_fields = ['query_id', 'created_at']


class ContentProcessingJobSerializer(serializers.ModelSerializer):
    """Serializer for ContentProcessingJob model."""
    
    class Meta:
        model = ContentProcessingJob
        fields = [
            'job_id', 'job_type', 'source_type', 'source_id',
            'status', 'progress', 'error_message', 'chunks_created',
            'processing_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['job_id', 'created_at', 'updated_at']


# Simplified serializers for list views
class ProjectListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Project list view."""
    primary_image = serializers.SerializerMethodField()
    tech_stack_list = serializers.ReadOnlyField(source='get_tech_stack_list')
    
    class Meta:
        model = Project
        fields = [
            'project_id', 'title', 'slug', 'description', 'tech_stack_list',
            'is_featured', 'difficulty_level', 'status', 'primary_image',
            'created_at'
        ]
        read_only_fields = ['project_id', 'slug', 'created_at']
    
    def get_primary_image(self, obj):
        """Get the primary image URL for the project."""
        primary_image = obj.get_primary_image()
        if primary_image:
            return primary_image.image.url
        return None


class ConversationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Conversation list view."""
    message_count = serializers.ReadOnlyField(source='get_message_count')
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'context_type', 'title', 'is_active',
            'message_count', 'last_message', 'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at']
    
    def get_last_message(self, obj):
        """Get the last message in the conversation."""
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'is_user': last_message.is_user,
                'timestamp': last_message.created_at
            }
        return None


class JobAnalysisListSerializer(serializers.ModelSerializer):
    """Simplified serializer for JobAnalysis list view."""
    match_level = serializers.ReadOnlyField(source='get_match_level')
    
    class Meta:
        model = JobAnalysis
        fields = [
            'analysis_id', 'job_title', 'company_name', 'overall_match_score',
            'match_level', 'processing_time', 'created_at'
        ]
        read_only_fields = ['analysis_id', 'created_at']
