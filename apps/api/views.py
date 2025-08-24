"""Views for the public API endpoints."""

from __future__ import annotations

import contextlib
import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from agents_core.agile_coach import AgileCoachAgent
from agents_core.product_owner import ProductOwnerAgent
from aiteam import __version__
from memory.short_term import ShortTermMemory
from orchestrator.tasks import run_retro

from .serializers import (
    ACFeedbackRequestSerializer,
    AgentThinkRequestSerializer,
    MemoryAppendSerializer,
    PlanRequestSerializer,
)


def health(request: HttpRequest) -> JsonResponse:
    """Simple health endpoint for readiness/liveness checks."""
    return JsonResponse({"status": "ok"})


@require_GET
def version(request: HttpRequest) -> JsonResponse:
    """Return application version."""
    return JsonResponse({"version": str(__version__)})


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


@require_POST
def memory_append(request: HttpRequest, agent: str) -> JsonResponse:
    """Append an item to short-term memory for an agent.

    Body JSON:
        {"item": "<text>"}
    """
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"non_field_errors": ["Invalid JSON body."]}}, status=400)

    ser = MemoryAppendSerializer(data=data)
    if not ser.is_valid():
        return JsonResponse({"errors": ser.errors}, status=400)

    stm = ShortTermMemory()
    item = ser.validated_data["item"]
    stm.append(agent, item)
    return JsonResponse({"agent": agent, "item": item}, status=201)


@require_POST
def plan(request: HttpRequest) -> JsonResponse:
    """Return a simple plan from the ProductOwnerAgent.

    Body JSON:
        {"description": "<text>"}
    """
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"non_field_errors": ["Invalid JSON body."]}}, status=400)

    ser = PlanRequestSerializer(data=data)
    if not ser.is_valid():
        return JsonResponse({"errors": ser.errors}, status=400)

    stm = ShortTermMemory()
    tasks = ProductOwnerAgent(name="po", role="Product Owner", memory=stm).plan_work(
        ser.validated_data["description"]
    )
    return JsonResponse({"tasks": tasks, "count": len(tasks)})


@require_POST
def ac_feedback(request: HttpRequest) -> JsonResponse:
    """Return feedback from the AgileCoachAgent for a list of tasks.

    Body JSON:
        {"tasks": ["..."]}
    """
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"non_field_errors": ["Invalid JSON body."]}}, status=400)

    ser = ACFeedbackRequestSerializer(data=data)
    if not ser.is_valid():
        return JsonResponse({"errors": ser.errors}, status=400)

    stm = ShortTermMemory()
    feedback = AgileCoachAgent(name="ac", role="Agile Coach", memory=stm).feedback_on_plan(
        ser.validated_data["tasks"]
    )
    return JsonResponse({"feedback": feedback})


@require_POST
def agent_think(request: HttpRequest) -> JsonResponse:
    """Have a core agent generate a thought for a goal and record it.

    Body JSON:
        {"agent": "po"|"ac", "goal": "<text>"}
    """
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"non_field_errors": ["Invalid JSON body."]}}, status=400)

    ser = AgentThinkRequestSerializer(data=data)
    if not ser.is_valid():
        return JsonResponse({"errors": ser.errors}, status=400)

    stm = ShortTermMemory()
    if ser.validated_data["agent"] == "po":
        agent = ProductOwnerAgent(name="po", role="Product Owner", memory=stm)
    else:
        agent = AgileCoachAgent(name="ac", role="Agile Coach", memory=stm)
    thought = agent.think(ser.validated_data["goal"])
    return JsonResponse({"thought": thought})


@require_POST
def retro_run(request: HttpRequest) -> JsonResponse:
    """Schedule a background retrospective task.

    Returns 202 Accepted. Attempts to schedule via Celery; falls back to local
    execution if scheduling fails.
    """
    scheduled = False
    try:
        # Prefer scheduling; may fail if no broker configured
        run_retro.delay()  # type: ignore[call-arg]
        scheduled = True
    except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
        # Execute locally without broker as a fallback (non-fatal)
        with contextlib.suppress(Exception):  # pragma: no cover - defensive
            run_retro.apply(args=())  # type: ignore[attr-defined]
    return JsonResponse({"accepted": True, "scheduled": scheduled}, status=202)
