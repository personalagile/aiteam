"""URL patterns for the public API endpoints."""

from __future__ import annotations

from django.urls import path

from .views import (
    ac_feedback,
    agent_think,
    health,
    memory_append,
    memory_history,
    plan,
    retro_run,
    version,
)

urlpatterns = [
    path("health", health, name="health"),
    path("version", version, name="version"),
    path("memory/<str:agent>/history", memory_history, name="memory-history"),
    path("memory/<str:agent>/append", memory_append, name="memory-append"),
    path("plan", plan, name="plan"),
    path("ac_feedback", ac_feedback, name="ac-feedback"),
    path("agent/think", agent_think, name="agent-think"),
    path("retro/run", retro_run, name="retro-run"),
]
