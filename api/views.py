from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, throttle_classes, action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import logging
import asyncio
from asgiref.sync import sync_to_async
import time

from .serializers import (
    ProfileSerializer, ProjectSerializer, ProjectListSerializer,
    VisitorSessionSerializer, PageViewSerializer, VisitorInteractionSerializer,
    ConversationSerializer, ConversationListSerializer, MessageSerializer,
    ChatSessionSerializer, JobAnalysisSerializer, JobAnalysisListSerializer,
    SkillsMatchSerializer, JobRecommendationSerializer, DocumentChunkSerializer,
    EmbeddingCacheSerializer, RAGQuerySerializer, ContentProcessingJobSerializer
)
from core.models import Profile
from projects.models import Project, ProjectImage
from visitors.models import VisitorSession, PageView, VisitorInteraction
from ai_chat.models import Conversation, Message, ChatSession
from job_matching.models import JobAnalysis, SkillsMatch, JobRecommendation
from ai_services.models import DocumentChunk, EmbeddingCache, RAGQuery, ContentProcessingJob
from ai_services.rag_service import RAGService
from job_matching.analysis_service import JobAnalysisService
from .caching import api_cache_service, cache_api_response, cache_statistics
from core.query_optimization import query_optimizer

logger = logging.getLogger(__name__)


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Profile model - read-only for public API."""
    queryset = Profile.objects.filter(is_active=True)
    serializer_class = ProfileSerializer
    lookup_field = 'profile_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return active profiles with optimized queries."""
        return query_optimizer.get_optimized_profiles(active_only=True)


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Project model with filtering and search."""
    serializer_class = ProjectSerializer
    lookup_field = 'project_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return projects with optimized queries and filtering."""
        # Get base optimized queryset
        queryset = query_optimizer.get_optimized_projects()
        
        # Filter by featured projects
        featured = self.request.query_params.get('featured', None)
        if featured is not None:
            queryset = queryset.filter(is_featured=featured.lower() == 'true')
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by difficulty level
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(detailed_description__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views."""
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    @action(detail=True, methods=['get'])
    def images(self, request, project_id=None):
        """Get all images for a specific project."""
        project = self.get_object()
        images = project.images.all()
        serializer = ProjectImageSerializer(images, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get all featured projects."""
        featured_projects = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(featured_projects, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_statistics('project_statistics')
    def stats(self, request):
        """Get project statistics with caching."""
        stats = query_optimizer.get_project_statistics()
        return Response(stats)


class VisitorSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for VisitorSession model - read-only for analytics."""
    queryset = VisitorSession.objects.all()
    serializer_class = VisitorSessionSerializer
    lookup_field = 'session_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return visitor sessions with optimized queries."""
        return VisitorSession.objects.prefetch_related('pageviews', 'visitorinteractions')
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get visitor analytics."""
        queryset = self.get_queryset()
        
        # Time range filter
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=since)
        
        analytics = {
            'total_sessions': queryset.count(),
            'unique_visitors': queryset.values('ip_address').distinct().count(),
            'recruiter_sessions': queryset.filter(is_recruiter=True).count(),
            'bot_sessions': queryset.filter(is_bot=True).count(),
            'average_page_views': queryset.aggregate(avg=Avg('page_views'))['avg'] or 0,
            'device_distribution': dict(queryset.values('device_type').annotate(count=Count('id')).values_list('device_type', 'count')),
            'browser_distribution': dict(queryset.values('browser').annotate(count=Count('id')).values_list('browser', 'count')),
        }
        
        return Response(analytics)


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Conversation model."""
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    lookup_field = 'conversation_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return conversations with optimized queries."""
        return Conversation.objects.select_related('visitor_session', 'project').prefetch_related('messages')
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views."""
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
    
    @action(detail=True, methods=['get'])
    def messages(self, request, conversation_id=None):
        """Get all messages for a specific conversation."""
        conversation = self.get_object()
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_statistics('conversation_statistics')
    def stats(self, request):
        """Get conversation statistics with caching."""
        days = int(request.query_params.get('days', 30))
        stats = query_optimizer.get_conversation_statistics(days=days)
        return Response(stats)


class JobAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for JobAnalysis model."""
    queryset = JobAnalysis.objects.all()
    serializer_class = JobAnalysisSerializer
    lookup_field = 'analysis_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return job analyses with optimized queries."""
        return JobAnalysis.objects.select_related('visitor_session').prefetch_related('skills_matches', 'recommendations')
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views."""
        if self.action == 'list':
            return JobAnalysisListSerializer
        return JobAnalysisSerializer
    
    @action(detail=False, methods=['get'])
    @cache_statistics('job_analysis_statistics')
    def stats(self, request):
        """Get job analysis statistics with caching."""
        days = int(request.query_params.get('days', 30))
        stats = query_optimizer.get_job_analysis_statistics(days=days)
        return Response(stats)


class DocumentChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DocumentChunk model."""
    queryset = DocumentChunk.objects.filter(is_active=True)
    serializer_class = DocumentChunkSerializer
    lookup_field = 'chunk_id'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return document chunks with filtering."""
        queryset = DocumentChunk.objects.filter(is_active=True)
        
        # Filter by source type
        source_type = self.request.query_params.get('source_type', None)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # Filter by source ID
        source_id = self.request.query_params.get('source_id', None)
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        
        return queryset


# Custom rate limiting for chat endpoints
class ChatRateThrottle(AnonRateThrottle):
    rate = '30/hour'


@api_view(['GET'])
def api_status(request):
    """API status endpoint."""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


@api_view(['GET'])
@cache_api_response('cache_management')
def cache_stats(request):
    """Get comprehensive cache statistics."""
    try:
        stats = api_cache_service.get_cache_stats()
        return Response(stats)
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        return Response(
            {'error': 'Failed to get cache statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def clear_cache(request):
    """Clear cache entries."""
    try:
        cache_type = request.data.get('cache_type', 'all')
        
        if cache_type == 'all':
            success = api_cache_service.clear_all_cache()
        else:
            # Clear specific cache type
            success = api_cache_service.invalidate_cache_pattern(cache_type)
        
        if success:
            return Response({'message': f'Cache cleared successfully: {cache_type}'})
        else:
            return Response(
                {'error': 'Failed to clear cache'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        return Response(
            {'error': 'Failed to clear cache'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def api_stats(request):
    """API statistics endpoint."""
    stats = {
        'profiles': Profile.objects.filter(is_active=True).count(),
        'projects': Project.objects.count(),
        'conversations': Conversation.objects.count(),
        'job_analyses': JobAnalysis.objects.count(),
        'document_chunks': DocumentChunk.objects.filter(is_active=True).count(),
        'visitor_sessions': VisitorSession.objects.count(),
    }
    
    return Response(stats)


@api_view(['GET'])
def search(request):
    """Global search endpoint across multiple models."""
    query = request.query_params.get('q', '')
    if not query:
        return Response({'error': 'Query parameter "q" is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = {
        'projects': [],
        'profiles': [],
    }
    
    # Search projects
    projects = Project.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query) |
        Q(detailed_description__icontains=query)
    )[:10]
    results['projects'] = ProjectListSerializer(projects, many=True).data
    
    # Search profiles
    profiles = Profile.objects.filter(
        Q(name__icontains=query) | 
        Q(bio__icontains=query)
    )[:5]
    results['profiles'] = ProfileSerializer(profiles, many=True).data
    
    return Response(results)


# Chat API Endpoints
@api_view(['POST'])
@throttle_classes([ChatRateThrottle])
def chat_endpoint(request):
    """Real-time chat endpoint with RAG integration."""
    try:
        question = request.data.get('question', '').strip()
        context_type = request.data.get('context_type', 'general')
        project_id = request.data.get('project_id', None)
        
        if not question:
            return Response(
                {'error': 'Question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate context type
        valid_context_types = ['general', 'project', 'experience', 'skills']
        if context_type not in valid_context_types:
            return Response(
                {'error': f'Invalid context_type. Must be one of: {", ".join(valid_context_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate project_id if provided
        project = None
        if project_id:
            try:
                project = Project.objects.get(project_id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {'error': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Process with RAG service
        rag_service = RAGService()
        start_time = time.time()
        
        try:
            # Call RAG service directly (it's already synchronous)
            result = rag_service.query(
                question, 
                context_type=context_type, 
                source_id=project_id if project_id else None
            )
            
            response_time = time.time() - start_time
            
            # Add response time to result
            result['response_time'] = round(response_time, 2)
            
            # Save conversation if visitor session exists
            if hasattr(request, 'visitor_session') and request.visitor_session:
                save_chat_message(
                    request.visitor_session, 
                    question, 
                    result, 
                    context_type, 
                    project
                )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"RAG service error: {str(e)}")
            return Response({
                'answer': 'I apologize, but I encountered an error processing your question. Please try again.',
                'confidence': 0.0,
                'response_time': round(time.time() - start_time, 2),
                'error': 'Internal processing error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@throttle_classes([ChatRateThrottle])
def chat_with_timeout(request):
    """Chat endpoint with timeout handling for better user experience."""
    try:
        question = request.data.get('question', '').strip()
        context_type = request.data.get('context_type', 'general')
        project_id = request.data.get('project_id', None)
        timeout = request.data.get('timeout', 10)  # Default 10 seconds
        
        if not question:
            return Response(
                {'error': 'Question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate timeout
        if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 30:
            timeout = 10
        
        # Validate context type
        valid_context_types = ['general', 'project', 'experience', 'skills']
        if context_type not in valid_context_types:
            return Response(
                {'error': f'Invalid context_type. Must be one of: {", ".join(valid_context_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate project_id if provided
        project = None
        if project_id:
            try:
                project = Project.objects.get(project_id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {'error': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Process with timeout
        rag_service = RAGService()
        start_time = time.time()
        
        try:
            # Create async task with timeout
            async def process_chat():
                return await sync_to_async(rag_service.query)(
                    question, 
                    context_type=context_type, 
                    source_id=project_id if project_id else None
                )
            
            # Run with timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(process_chat(), timeout=timeout)
                )
            finally:
                loop.close()
            
            response_time = time.time() - start_time
            result['response_time'] = round(response_time, 2)
            
            # Save conversation if visitor session exists
            if hasattr(request, 'visitor_session') and request.visitor_session:
                save_chat_message(
                    request.visitor_session, 
                    question, 
                    result, 
                    context_type, 
                    project
                )
            
            return Response(result)
            
        except asyncio.TimeoutError:
            return Response({
                'answer': 'I\'m taking a bit longer to process your question. Please try again or rephrase your question.',
                'confidence': 0.0,
                'response_time': timeout,
                'timeout': True,
                'retry': True
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
            
        except Exception as e:
            logger.error(f"RAG service error: {str(e)}")
            return Response({
                'answer': 'I apologize, but I encountered an error processing your question. Please try again.',
                'confidence': 0.0,
                'response_time': round(time.time() - start_time, 2),
                'error': 'Internal processing error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def save_chat_message(visitor_session, question, result, context_type, project=None):
    """Save chat conversation to database."""
    try:
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            visitor_session=visitor_session,
            context_type=context_type,
            project=project,
            defaults={
                'is_active': True,
                'title': f"{context_type.title()} Chat"
            }
        )
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            content=question,
            is_user=True,
            message_type='user_question'
        )
        
        # Save AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            content=result.get('answer', ''),
            is_user=False,
            message_type='ai_response',
            response_time=result.get('response_time', 0),
            confidence_score=result.get('confidence', 0.0),
            context_chunks_used=result.get('chunks_used', []),
            tokens_used=result.get('tokens_used', 0)
        )
        
        # Update conversation
        conversation.last_message_at = timezone.now()
        conversation.message_count = conversation.messages.count()
        conversation.save(update_fields=['last_message_at', 'message_count'])
        
        # Create visitor interaction
        VisitorInteraction.objects.create(
            visitor_session=visitor_session,
            interaction_type='chat_message',
            details={
                'question': question[:200],  # Truncate for storage
                'context_type': context_type,
                'project_id': str(project.project_id) if project else None,
                'response_time': result.get('response_time', 0),
                'confidence': result.get('confidence', 0.0)
            }
        )
        
        logger.info(f"Chat message saved: {user_message.message_id} -> {ai_message.message_id}")
        
    except Exception as e:
        logger.error(f"Error saving chat message: {str(e)}")


@api_view(['GET'])
def chat_history(request):
    """Get chat history for current visitor session."""
    try:
        if not hasattr(request, 'visitor_session') or not request.visitor_session:
            return Response(
                {'error': 'No visitor session found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get conversations for this visitor
        conversations = Conversation.objects.filter(
            visitor_session=request.visitor_session
        ).select_related('project').prefetch_related('messages').order_by('-created_at')
        
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Chat history error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def clear_chat_history(request):
    """Clear chat history for current visitor session."""
    try:
        if not hasattr(request, 'visitor_session') or not request.visitor_session:
            return Response(
                {'error': 'No visitor session found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deactivate conversations instead of deleting
        conversations = Conversation.objects.filter(
            visitor_session=request.visitor_session
        )
        
        count = conversations.count()
        conversations.update(is_active=False)
        
        return Response({
            'message': f'Cleared {count} conversations',
            'conversations_cleared': count
        })
        
    except Exception as e:
        logger.error(f"Clear chat history error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ChatRateThrottle(AnonRateThrottle):
    """Custom rate throttle for chat endpoints."""
    rate = '30/hour'


@api_view(['POST'])
@throttle_classes([ChatRateThrottle])
def job_analysis_endpoint(request):
    """Job requirements analysis endpoint with file upload support."""
    try:
        job_text = request.data.get('job_requirements', '')
        uploaded_file = request.FILES.get('job_file')
        
        if not job_text and not uploaded_file:
            return Response(
                {'error': 'Job requirements text or file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file if provided
        if uploaded_file:
            # Check file size (10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:
                return Response(
                    {'error': 'File too large. Maximum size: 10MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check file type
            allowed_extensions = ['.pdf', '.txt', '.docx']
            file_extension = uploaded_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                return Response(
                    {'error': f'Unsupported file type. Supported: {", ".join(allowed_extensions)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Process job analysis
        analysis_service = JobAnalysisService()
        start_time = time.time()
        
        try:
            # Call analysis service directly (it's already synchronous)
            result = analysis_service.analyze_job(
                job_text, 
                uploaded_file, 
                getattr(request, 'visitor_session', None)
            )
            
            response_time = time.time() - start_time
            result['response_time'] = round(response_time, 2)
            
            # Create visitor interaction
            if hasattr(request, 'visitor_session') and request.visitor_session:
                VisitorInteraction.objects.create(
                    visitor_session=request.visitor_session,
                    interaction_type='job_analysis',
                    details={
                        'job_title': result.get('job_details', {}).get('title', ''),
                        'company': result.get('job_details', {}).get('company', ''),
                        'match_score': result.get('match_scores', {}).get('overall', 0),
                        'match_level': result.get('match_level', ''),
                        'processing_time': result['response_time']
                    }
                )
            
            return Response(result)
            
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Job analysis processing error: {str(e)}")
            return Response({
                'error': 'Error processing job analysis. Please try again.',
                'response_time': round(time.time() - start_time, 2)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Job analysis endpoint error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def job_analysis_history(request):
    """Get job analysis history for current visitor session."""
    try:
        if not hasattr(request, 'visitor_session') or not request.visitor_session:
            return Response(
                {'error': 'No visitor session found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get job analyses for this visitor
        analyses = JobAnalysis.objects.filter(
            visitor_session=request.visitor_session
        ).select_related().prefetch_related('skills_matches', 'recommendations').order_by('-created_at')
        
        serializer = JobAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Job analysis history error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def job_analysis_detail(request, analysis_id):
    """Get detailed job analysis by ID."""
    try:
        analysis = get_object_or_404(
            JobAnalysis.objects.select_related().prefetch_related('skills_matches', 'recommendations'),
            analysis_id=analysis_id
        )
        
        serializer = JobAnalysisSerializer(analysis)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Job analysis detail error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def job_analysis_stats(request):
    """Get job analysis statistics."""
    try:
        # Get overall statistics
        total_analyses = JobAnalysis.objects.count()
        
        # Match level distribution
        match_levels = {
            'excellent': JobAnalysis.objects.filter(overall_match_score__gte=90).count(),
            'good': JobAnalysis.objects.filter(overall_match_score__gte=70, overall_match_score__lt=90).count(),
            'fair': JobAnalysis.objects.filter(overall_match_score__gte=50, overall_match_score__lt=70).count(),
            'poor': JobAnalysis.objects.filter(overall_match_score__lt=50).count(),
        }
        
        # Average scores
        avg_scores = JobAnalysis.objects.aggregate(
            avg_overall=Avg('overall_match_score'),
            avg_skills=Avg('skills_match_score'),
            avg_experience=Avg('experience_match_score'),
            avg_education=Avg('education_match_score')
        )
        
        # Recent analyses (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_analyses = JobAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
        
        return Response({
            'total_analyses': total_analyses,
            'recent_analyses': recent_analyses,
            'match_level_distribution': match_levels,
            'average_scores': {
                'overall': round(avg_scores['avg_overall'] or 0, 1),
                'skills': round(avg_scores['avg_skills'] or 0, 1),
                'experience': round(avg_scores['avg_experience'] or 0, 1),
                'education': round(avg_scores['avg_education'] or 0, 1),
            }
        })
        
    except Exception as e:
        logger.error(f"Job analysis stats error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )