"""Product Owner agent implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from memory.long_term import KnowledgeGraph

from .base import BaseAgent
from .llm import detect_llm


@dataclass(slots=True)
class ProductOwnerAgent(BaseAgent):
    """Product Owner agent responsible for backlog and stakeholder alignment."""

    def plan_work(self, description: str) -> list[str]:
        """Break a description into coarse-grained tasks and record planning.

        If an LLM is enabled (via environment), attempt to produce actionable
        tasks. Fallback is only used when no tasks can be parsed.
        """
        tasks, _debug = self.plan_work_debug(description)
        return tasks

    def plan_work_debug(self, description: str) -> tuple[list[str], dict[str, object]]:
        """Like plan_work() but also returns debug info including raw LLM text.

        Returns (tasks, debug_dict).
        """
        self.observe(f"planning: {description}")
        tasks: list[str] = []
        provider = self.llm or detect_llm()
        prompt = (
            "You are a Product Owner. Create a list of actionable tasks for the "
            "following description.\n"
            f"Description: {description}\n"
            "Return output as lines starting with '- '. No extra text."
        )
        debug: dict[str, object] = {
            "provider": provider.__class__.__name__ if provider else None,
            "prompt": prompt,
            "raw_response": None,
            "parsed_lines": [],
            "used_fallback": False,
        }
        if provider is not None:
            try:
                text = provider.generate(prompt)
                debug["raw_response"] = text
                # Accept '-', '*', '•', en dash '–', with optional escape '\-' from LLM,
                # or numbered lists like '1.'/'1)'.
                pattern = r"^\s*(?:\\?[-*•–]|\d+[\.)])\s+(.*)$"
                parsed: list[str] = []
                for line in text.splitlines():
                    line = line.strip()
                    m = re.match(pattern, line)
                    if m:
                        parsed.append(m.group(1).strip())
                debug["parsed_lines"] = parsed
                # Use all parsed tasks without limiting to two
                tasks = [t for t in parsed if t]
            except RuntimeError:  # pragma: no cover - defensive
                tasks = []
                debug["used_fallback"] = True
        # Deterministic fallback only if no tasks could be parsed
        if len(tasks) == 0:
            tasks = [
                f"Define acceptance criteria for: {description}",
                f"Identify needed experts for: {description}",
            ]
            debug["used_fallback"] = True
        # Store a brief note in long-term memory (no-op if Neo4j not configured)
        try:
            kg = KnowledgeGraph()
            kg.upsert_note(self.name, f"planned {len(tasks)} task(s) for: {description}")
        except Exception:  # pragma: no cover - defensive  # pylint: disable=broad-exception-caught
            pass
        return tasks, debug
