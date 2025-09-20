"""
Main URL configuration for portfolio_site project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('health/', include('core.urls')),
    
    # Production monitoring endpoints (commented out for testing)
    # path('health/status/', include('api.monitoring')),
    # path('ready/', include('api.monitoring')),
    # path('liveness/', include('api.monitoring')),
    # path('metrics/', include('api.monitoring')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)