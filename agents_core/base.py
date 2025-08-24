"""Base classes and protocols for agent implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Memory(Protocol):
    """Protocol that defines the short-term memory interface."""

    def append(self, agent: str, item: str) -> None:
        """Persist an item for the given agent."""
        pass  # pragma: no cover - protocol stub

    def history(self, agent: str, limit: int = 20) -> list[str]:
        """Return the last ``limit`` items for the agent."""
        pass  # pragma: no cover - protocol stub


@dataclass(slots=True)
class BaseAgent:
    """Base class for all agents.

    Attributes:
        name: Unique agent name.
        role: Short description of the agent's responsibility.
        memory: Short-term memory interface.
    """

    name: str
    role: str
    memory: Memory | None = None

    def observe(self, content: str) -> None:
        """Record an observation to the agent's memory if available."""
        if self.memory:
            self.memory.append(self.name, content)

    def think(self, goal: str) -> str:  # pragma: no cover - demo logic
        """Very simple stub: echoes goal with role context."""
        thought = f"[{self.role}] Considering: {goal}"
        self.observe(thought)
        return thought

    def act(self, goal: str) -> str:  # pragma: no cover - demo logic
        """Return a simple action message and record it in memory."""
        action = f"[{self.role}] Action for: {goal}"
        self.observe(action)
        return action
