"""ASGI configuration for the AITEAM project using Django Channels.

This module initializes the Django ASGI application and wires the websocket
protocol to our chat app routing. The import of ``apps.chat.routing`` occurs
after Django setup on purpose to avoid premature app loading, hence the
import-position suppression.
"""

from __future__ import annotations

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiteam.settings")

django_asgi_app = get_asgi_application()

import apps.chat.routing  # noqa: E402  (import after Django setup)  # pylint: disable=wrong-import-position

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(apps.chat.routing.websocket_urlpatterns)),
    }
)
