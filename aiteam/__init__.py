"""AITEAM Django project init.

Exposes the Celery app for Django autodiscovery.
"""

from __future__ import annotations

from .celery import app as celery_app

# Keep in sync with project.version in pyproject.toml
__version__ = "0.1.0"

__all__ = ["celery_app", "__version__"]
