"""Celery tasks for orchestrating background agent workflows.

Includes:

- ``run_retro``: minimal retrospective that optionally records a note in
  long-term memory (no-op if Neo4j is not configured).
- ``run_experts_pipeline``: orchestrates Product Owner planning -> dynamic
  expert selection -> parallel expert preparation, returning aggregated
  results and optional debug information.
"""

from __future__ import annotations

import json
import structlog
from celery import group, shared_task

from agents_core.agile_coach import AgileCoachAgent
from agents_core.dynamic_expert import (
    DynamicExpertAgent,
    select_experts_from_tasks,
)
from agents_core.product_owner import ProductOwnerAgent
from memory.long_term import KnowledgeGraph
from memory.short_term import ShortTermMemory

logger = structlog.get_logger(__name__)


def _retro_insights(stm: ShortTermMemory) -> dict[str, object]:
    """Compute simple retrospective insights from short-term memory.

    Currently summarizes recent activity for core agents ("po", "ac").
    Returns a dict suitable for structured logging and optional persistence.
    """
    agents = ("po", "ac")
    summaries: list[dict[str, object]] = []
    for agent in agents:
        hist = stm.history(agent, limit=5)
        summaries.append(
            {
                "agent": agent,
                "count": len(hist),
                "last": hist[-1] if hist else "",
            }
        )
    return {"summaries": summaries}


@shared_task
def run_retro() -> str:
    """Run a lightweight retrospective: schedule and record a note.

    Uses ``AgileCoachAgent.schedule_retro()`` to simulate a retro action and
    records a brief note to long-term memory when available. Returns "ok" to
    remain backward compatible with existing API/tests.
    """
    logger.info("retro.run", status="started")

    # Short-term memory shared across this small workflow
    stm = ShortTermMemory()

    # Attempt to schedule a retrospective via the Agile Coach agent
    msg = "retro scheduled"
    try:
        ac = AgileCoachAgent(name="ac", role="Agile Coach", memory=stm)
        msg = ac.schedule_retro()
    except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
        pass

    # Record a brief note in long-term memory (no-op if Neo4j not configured)
    try:
        kg = KnowledgeGraph()
        kg.upsert_note("ac", f"retro: {msg}")
    except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
        pass

    # Derive and log lightweight insights
    insights = _retro_insights(stm)
    logger.info("retro.insights", insights=insights)

    # Persist insights as a compact note (no-op if Neo4j not configured)
    try:
        kg = KnowledgeGraph()
        kg.upsert_note("ac", f"retro_insights: {json.dumps(insights, separators=(',', ':'))}")
    except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
        pass

    logger.info("retro.run", status="finished")
    return "ok"


@shared_task
def expert_prepare(expertise: str, user_msg: str) -> dict[str, str]:
    """Prepare a single expert for the given user message.

    Returns a mapping with the expert name and the preparation message.
    """
    stm = ShortTermMemory()
    agent = DynamicExpertAgent(
        name=f"expert-{expertise}", role="Expert", expertise=expertise, memory=stm
    )
    message = agent.solve(f"Prepare for: {user_msg}")
    return {"expert": expertise, "message": message}


@shared_task
def run_experts_pipeline(description: str, debug: bool = False) -> dict[str, object]:
    """End-to-end experts pipeline.

    Steps:
    1) Plan tasks using ``ProductOwnerAgent``.
    2) Select experts from tasks using heuristic + optional LLM.
    3) Run expert preparation in parallel and aggregate results.
    """
    logger.info("experts.pipeline", stage="start")

    # Short-term memory shared across agents in this pipeline
    stm = ShortTermMemory()

    # 1) Plan
    po = ProductOwnerAgent(name="po", role="Product Owner", memory=stm)
    if debug and hasattr(po, "plan_work_debug"):
        tasks, plan_dbg = po.plan_work_debug(description)  # type: ignore[attr-defined]
    else:
        tasks = po.plan_work(description)
        plan_dbg = None

    # 2) Select experts
    specs, sel_dbg = select_experts_from_tasks(tasks)
    expert_names = [s.expertise for s in specs]

    # 3) Prepare experts in parallel
    results: list[dict[str, str]] = []
    try:
        # Execute synchronously in-process to avoid requiring a broker in tests/local
        job_result = group(expert_prepare.s(name, description) for name in expert_names).apply()
        results = job_result.get()
    except Exception:  # pragma: no cover  # pylint: disable=broad-exception-caught
        # Run inline without a broker (sequential but reliable in dev/tests)
        for name in expert_names:
            results.append(expert_prepare.apply(args=(name, description)).get())

    # Aggregate to a deterministic mapping
    results_map: dict[str, str] = {item["expert"]: item["message"] for item in results}

    payload: dict[str, object] = {
        "tasks": tasks,
        "experts": expert_names,
        "results": results_map,
    }
    if debug:
        payload["_debug"] = {"plan": plan_dbg, "selection": sel_dbg}

    logger.info("experts.pipeline", stage="done", experts=len(expert_names), tasks=len(tasks))
    return payload
