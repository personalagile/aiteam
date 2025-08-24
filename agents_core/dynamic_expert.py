"""Dynamic expert agent implementation."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent


@dataclass(slots=True)
class DynamicExpertAgent(BaseAgent):
    """Cross-functional expert agent spun up on demand."""

    expertise: str = "generalist"

    def solve(self, task: str) -> str:
        """Solve a given task using the agent's expertise and record it."""
        msg = f"[{self.expertise}] solving: {task}"
        self.observe(msg)
        return msg
