"""
URL configuration for async_service project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/async/', include('chronicle_processor.urls')),
]

