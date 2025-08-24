"""Views for the chat UI."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def chat_index(request: HttpRequest) -> HttpResponse:
    """Render the minimal chat UI."""
    return render(request, "chat/index.html", {})
