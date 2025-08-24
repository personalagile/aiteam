"""Agile Coach agent implementation."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent
from memory.long_term import KnowledgeGraph


@dataclass(slots=True)
class AgileCoachAgent(BaseAgent):
    """Agile Coach agent facilitating ceremonies and process improvements."""

    def schedule_retro(self) -> str:
        """Schedule the next retrospective and record it in memory."""
        msg = "Scheduled next retrospective"
        self.observe(msg)
        return msg

    def feedback_on_plan(self, tasks: list[str]) -> str:
        """Provide brief feedback on a PO plan and record it in memory.

        The feedback is intentionally simple and focuses on healthy agile
        practices, such as acceptance criteria, slicing work, and expert
        collaboration.
        """
        if not tasks:
            advice = "Bitte formuliere mindestens eine umsetzbare Aufgabe."
        else:
            actionable = any("acceptance" in t.lower() or "akzeptanz" in t.lower() for t in tasks)
            experts = any("expert" in t.lower() or "experte" in t.lower() for t in tasks)
            suggestions: list[str] = []
            if not actionable:
                suggestions.append("Definiere messbare Akzeptanzkriterien.")
            if not experts:
                suggestions.append("Beziehe die richtigen Expert:innen frühzeitig ein.")
            suggestions.append("Schneide Arbeit in kleine, testbare Inkremente.")
            advice = " ".join(suggestions)
        self.observe(f"ac_feedback: {advice}")
        # Store a brief feedback note in long-term memory (no-op if Neo4j not configured)
        try:
            kg = KnowledgeGraph()
            kg.upsert_note(self.name, f"feedback: {advice}")
        except Exception:  # pragma: no cover - defensive
            pass
        return advice
