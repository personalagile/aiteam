"""Views for the public API endpoints."""

from __future__ import annotations

import contextlib
import json
import os
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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

# --- Optional API security (token auth + simple rate limiting) ---

_RL_LOCK = threading.Lock()
_RL_BUCKETS: dict[str, list[float]] = {}


def _auth_enabled() -> bool:
    return os.getenv("API_ENABLE_AUTH", "0").lower() in {"1", "true", "yes"}


def _rate_limit_enabled() -> bool:
    return os.getenv("API_RATE_LIMIT_ENABLED", "0").lower() in {"1", "true", "yes"}


def _rate_limit_per_min() -> int:
    try:
        return max(1, int(os.getenv("API_RATE_LIMIT_PER_MIN", "60")))
    except ValueError:
        return 60


def _get_token_from_request(request: HttpRequest) -> str:
    return request.META.get("HTTP_X_API_TOKEN", "")


def _get_requester_id(request: HttpRequest) -> str:
    token = _get_token_from_request(request)
    if token:
        return f"token:{token[:8]}"
    return f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"


def api_guard(view: Callable[[HttpRequest], JsonResponse]) -> Callable[[HttpRequest], JsonResponse]:
    """Decorator adding optional token auth and rate limiting to an API view."""

    @wraps(view)
    def _wrapped(
        request: HttpRequest, *args: Any, **kwargs: Any
    ) -> JsonResponse:  # type: ignore[override]
        # Token auth (optional)
        if _auth_enabled():
            expected = os.getenv("API_TOKEN", "")
            provided = _get_token_from_request(request)
            if not expected or provided != expected:
                return JsonResponse({"errors": {"auth": ["Unauthorized."]}}, status=401)

        # Rate limiting (optional)
        if _rate_limit_enabled():
            key = _get_requester_id(request)
            now = time.time()
            window = 60.0
            with _RL_LOCK:
                bucket = _RL_BUCKETS.setdefault(key, [])
                # prune
                cutoff = now - window
                prune_count = next(
                    (idx for idx, ts in enumerate(bucket) if ts >= cutoff), len(bucket)
                )
                if prune_count:
                    del bucket[:prune_count]
                if len(bucket) >= _rate_limit_per_min():
                    return JsonResponse({"errors": {"rate": ["Too Many Requests."]}}, status=429)
                bucket.append(now)

        return view(request, *args, **kwargs)

    return _wrapped


def health(request: HttpRequest) -> JsonResponse:
    """Simple health endpoint for readiness/liveness checks."""
    return JsonResponse({"status": "ok"})


@require_GET
@api_guard
def version(request: HttpRequest) -> JsonResponse:
    """Return application version."""
    return JsonResponse({"version": str(__version__)})


@require_GET
@api_guard
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


@csrf_exempt
@require_POST
@api_guard
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


@csrf_exempt
@require_POST
@api_guard
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
    agent = ProductOwnerAgent(name="po", role="Product Owner", memory=stm)
    debug_flag = str(request.GET.get("debug", "0")).strip().lower() in {"1", "true", "yes", "on"}
    if debug_flag:
        tasks, dbg = agent.plan_work_debug(ser.validated_data["description"])
        return JsonResponse({"tasks": tasks, "count": len(tasks), "_debug": dbg})
    tasks = agent.plan_work(ser.validated_data["description"])
    return JsonResponse({"tasks": tasks, "count": len(tasks)})


@csrf_exempt
@require_POST
@api_guard
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


@csrf_exempt
@require_POST
@api_guard
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
    debug_flag = str(request.GET.get("debug", "0")).strip().lower() in {"1", "true", "yes", "on"}
    if debug_flag and hasattr(agent, "think_debug"):
        thought, dbg = agent.think_debug(ser.validated_data["goal"])  # type: ignore[attr-defined]
        return JsonResponse({"thought": thought, "_debug": dbg})
    thought = agent.think(ser.validated_data["goal"])
    return JsonResponse({"thought": thought})


@csrf_exempt
@require_POST
@api_guard
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
