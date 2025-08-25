"""Base classes and protocols for agent implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .llm import LLM, detect_llm


class Memory(Protocol):
    """Protocol that defines the short-term memory interface."""

    def append(self, agent: str, item: str) -> None:
        """Persist an item for the given agent."""
        raise NotImplementedError  # pragma: no cover - protocol stub

    def history(self, agent: str, limit: int = 20) -> list[str]:
        """Return the last ``limit`` items for the agent."""
        raise NotImplementedError  # pragma: no cover - protocol stub


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
    llm: LLM | None = None

    def observe(self, content: str) -> None:
        """Record an observation to the agent's memory if available."""
        if self.memory:
            self.memory.append(self.name, content)

    def think(self, goal: str) -> str:  # pragma: no cover - demo logic
        """Generate a thought for the goal using an optional LLM.

        Falls back to a deterministic stub when no LLM is available or enabled.
        """
        thought, _debug = self.think_debug(goal)
        return thought

    def think_debug(
        self, goal: str
    ) -> tuple[str, dict[str, object]]:  # pragma: no cover - demo logic
        """Like think(), but also returns debug metadata including raw LLM output.

        Returns a tuple of (thought, debug_dict).
        """
        provider = self.llm or detect_llm()
        prompt = (
            f"Role: {self.role}. You are thinking step-by-step about the goal.\n"
            f"Goal: {goal}\n"
            "Return a single concise sentence capturing the next best thought."
        )
        debug: dict[str, object] = {
            "provider": provider.__class__.__name__ if provider else None,
            "prompt": prompt,
            "raw_response": None,
            "used_fallback": False,
        }
        if provider is not None:
            try:
                text = provider.generate(prompt).strip()
                debug["raw_response"] = text
                thought = text or f"[{self.role}] Considering: {goal}"
                if not text:
                    debug["used_fallback"] = True
            except RuntimeError:  # pragma: no cover - defensive
                thought = f"[{self.role}] Considering: {goal}"
                debug["used_fallback"] = True
        else:
            thought = f"[{self.role}] Considering: {goal}"
            debug["used_fallback"] = True
        self.observe(thought)
        return thought, debug

    def act(self, goal: str) -> str:  # pragma: no cover - demo logic
        """Return an action decision, optionally using an LLM, and record it.

        Mirrors `think()` behavior: try LLM first (if injected or detected),
        then fall back to a deterministic stub.
        """
        provider = self.llm or detect_llm()
        if provider is not None:
            prompt = (
                f"Role: {self.role}. Propose the next concrete action for the goal.\n"
                f"Goal: {goal}\n"
                "Return a single imperative sentence describing the action."
            )
            try:
                text = provider.generate(prompt).strip()
                action = text or f"[{self.role}] Action for: {goal}"
            except RuntimeError:  # pragma: no cover - defensive
                action = f"[{self.role}] Action for: {goal}"
        else:
            action = f"[{self.role}] Action for: {goal}"
        self.observe(action)
        return action
