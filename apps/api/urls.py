"""URL patterns for the public API endpoints."""

from __future__ import annotations

from django.urls import path

from .views import ac_feedback, health, memory_history, plan, retro_run

urlpatterns = [
    path("health", health, name="health"),
    path("memory/<str:agent>/history", memory_history, name="memory-history"),
    path("plan", plan, name="plan"),
    path("ac_feedback", ac_feedback, name="ac-feedback"),
    path("retro/run", retro_run, name="retro-run"),
]
