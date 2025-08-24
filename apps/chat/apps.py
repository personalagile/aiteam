"""Django app configuration for the chat application."""

from __future__ import annotations

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """AppConfig for chat-related Django components."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chat"
    verbose_name = "Chat"
