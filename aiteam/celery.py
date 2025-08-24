"""Celery application configuration for the AITEAM project.

This module initializes the Celery app, loads settings from Django, and
autodiscovers tasks across installed apps.
"""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiteam.settings")

app = Celery("aiteam")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self) -> str:  # pragma: no cover - example task only
    """Return a simple representation of the request for debugging."""
    return f"Request: {self.request!r}"
