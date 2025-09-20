"""
API URL patterns for the portfolio site.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
# from . import monitoring_views
from . import monitoring

# Create router and register viewsets
router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'visitor-sessions', views.VisitorSessionViewSet, basename='visitor-session')
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'job-analyses', views.JobAnalysisViewSet, basename='job-analysis')
router.register(r'document-chunks', views.DocumentChunkViewSet, basename='document-chunk')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('status/', views.api_status, name='api_status'),
    path('stats/', views.api_stats, name='api_stats'),
    path('search/', views.search, name='search'),
    
    # Cache management endpoints
    path('cache/stats/', views.cache_stats, name='cache_stats'),
    path('cache/clear/', views.clear_cache, name='clear_cache'),
    
    # Chat endpoints
    path('chat/', views.chat_endpoint, name='chat'),
    path('chat/timeout/', views.chat_with_timeout, name='chat_with_timeout'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('chat/clear/', views.clear_chat_history, name='clear_chat_history'),
    
    # Job analysis endpoints
    path('job-analysis/', views.job_analysis_endpoint, name='job_analysis'),
    path('job-analysis/history/', views.job_analysis_history, name='job_analysis_history'),
    path('job-analysis/<uuid:analysis_id>/', views.job_analysis_detail, name='job_analysis_detail'),
    path('job-analysis/stats/', views.job_analysis_stats, name='job_analysis_stats'),
    
    # Visitor analytics endpoints
    path('visitors/', include('visitors.urls')),
    
    # Monitoring and health check endpoints
    path('health/', monitoring.health_check, name='health_check'),
    path('ready/', monitoring.readiness_check, name='readiness_check'),
    path('liveness/', monitoring.liveness_check, name='liveness_check'),
    path('metrics/', monitoring.metrics, name='metrics'),
    
    # Legacy monitoring endpoints (commented out for testing)
    # path('status/', monitoring_views.system_status, name='system_status'),
    # path('health/<str:check_name>/', monitoring_views.health_check_detail, name='health_check_detail'),
    # path('performance/', monitoring_views.performance_metrics, name='performance_metrics'),
    # path('alerts/', monitoring_views.active_alerts, name='active_alerts'),
    # path('alerts/<str:alert_id>/resolve/', monitoring_views.resolve_alert, name='resolve_alert'),
    # path('alerts/history/', monitoring_views.alert_history, name='alert_history'),
    # path('security/events/', monitoring_views.security_events, name='security_events'),
    # path('monitoring/cycle/', monitoring_views.run_monitoring_cycle, name='run_monitoring_cycle'),
    # path('logs/', monitoring_views.api_logs, name='api_logs'),
]
