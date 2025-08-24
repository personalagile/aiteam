"""Celery tasks for orchestrating background agent workflows.

Currently contains a minimal retrospective task that optionally records a
note in long-term memory when Neo4j is configured.
"""

from __future__ import annotations

import structlog
from celery import shared_task

from memory.long_term import KnowledgeGraph

logger = structlog.get_logger(__name__)


@shared_task
def run_retro() -> str:
    """Run a retrospective across agents (stub)."""
    logger.info("retro.run", status="started")
    # Record a minimal note in long-term memory (no-op if Neo4j not configured)
    try:
        kg = KnowledgeGraph()
        kg.upsert_note("ac", "retro: improvements captured (stub)")
    except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
        pass
    logger.info("retro.run", status="finished")
    return "ok"
