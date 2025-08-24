"""URL patterns for the public API endpoints."""

from __future__ import annotations

from django.urls import path

from .views import health, memory_history

urlpatterns = [
    path("health", health, name="health"),
    path("memory/<str:agent>/history", memory_history, name="memory-history"),
]
