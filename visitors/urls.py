"""
URL patterns for visitor analytics and session management.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Session analytics endpoints
    path('analytics/sessions/', views.session_statistics, name='session_statistics'),
    path('analytics/sessions/<str:session_id>/', views.visitor_insights, name='visitor_insights'),
    path('analytics/real-time/', views.real_time_analytics, name='real_time_analytics'),
    path('analytics/engagement/', views.engagement_metrics, name='engagement_metrics'),
    path('analytics/behavior/', views.visitor_behavior_summary, name='visitor_behavior_summary'),
    path('analytics/popular-pages/', views.popular_pages, name='popular_pages'),
    
    # Current session endpoints
    path('session/current/', views.current_session_info, name='current_session_info'),
]
