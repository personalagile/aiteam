"""Views for the public API endpoints."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from memory.short_term import ShortTermMemory


def health(request: HttpRequest) -> JsonResponse:
    """Simple health endpoint for readiness/liveness checks."""
    return JsonResponse({"status": "ok"})


@require_GET
def memory_history(request: HttpRequest, agent: str) -> JsonResponse:
    """Return short-term memory history for ``agent``.

    Query parameters:
        limit: Optional int, number of last items to return (default 20, max 100).
    """
    try:
        limit = int(request.GET.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(100, limit))
    stm = ShortTermMemory()
    items = stm.history(agent, limit=limit)
    return JsonResponse({"agent": agent, "limit": limit, "items": items})
