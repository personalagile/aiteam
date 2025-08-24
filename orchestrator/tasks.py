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
    except Exception:  # pragma: no cover - defensive
        pass
    logger.info("retro.run", status="finished")
    return "ok"
