"""
backend/urls.py  —  Root URL configuration
All API routes live under /api/ and are handled by api/urls.py
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",   include("api.urls")),
]