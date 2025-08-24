"""ASGI routing for websocket endpoints of the chat app."""

from __future__ import annotations

from django.urls import re_path

from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/$", ChatConsumer.as_asgi()),
]
