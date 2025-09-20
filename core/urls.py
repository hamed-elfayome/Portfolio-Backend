"""
Core URL patterns for health checks and basic functionality.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.health_check, name='health_check'),
    path('ready/', views.readiness_check, name='readiness_check'),
]
