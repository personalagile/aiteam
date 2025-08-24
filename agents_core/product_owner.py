"""Product Owner agent implementation."""

from __future__ import annotations

from dataclasses import dataclass

from memory.long_term import KnowledgeGraph

from .base import BaseAgent


@dataclass(slots=True)
class ProductOwnerAgent(BaseAgent):
    """Product Owner agent responsible for backlog and stakeholder alignment."""

    def plan_work(self, description: str) -> list[str]:
        """Break a description into coarse-grained tasks and record planning."""
        self.observe(f"planning: {description}")
        # Stub: break description into two tasks
        tasks = [
            f"Define acceptance criteria for: {description}",
            f"Identify needed experts for: {description}",
        ]
        # Store a brief note in long-term memory (no-op if Neo4j not configured)
        try:
            kg = KnowledgeGraph()
            kg.upsert_note(self.name, f"planned {len(tasks)} task(s) for: {description}")
        except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
            pass
        return tasks
