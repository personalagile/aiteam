"""URL patterns for the chat app UI views."""

from __future__ import annotations

from django.urls import path

from .views import chat_index

urlpatterns = [
    path("", chat_index, name="chat_index"),
]
