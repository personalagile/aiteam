from __future__ import annotations

import json
from typing import Any

from django.test import Client

from agents_core.dynamic_expert import select_experts_from_tasks


def test_experts_run_non_it_domains() -> None:
    """API should return non-IT experts when description contains domain cues."""
    client = Client()
    # Contains cues for legal (gdpr), finance (budget), hr (onboarding)
    payload = {
        "description": (
            "Draft a GDPR-compliant data processing agreement, create the Q3 marketing budget, "
            "and update the onboarding policy for new hires."
        )
    }
    resp = client.post(
        "/api/experts/run",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    experts = set(data.get("experts", []))  # type: ignore[assignment]
    # At least one non-IT category should be present
    assert any(cat in experts for cat in {"legal", "finance", "hr", "marketing"})


def test_llm_unknown_role_preserved(monkeypatch: Any) -> None:
    """Unknown roles produced by the LLM should be preserved as-is (normalized)."""

    class FakeLLM:  # minimal provider shim
        def generate(self, prompt: str) -> str:  # noqa: D401
            return "- Market Research Analyst"

    import agents_core.dynamic_expert as de

    monkeypatch.setattr(de, "detect_llm", lambda: FakeLLM())

    specs, dbg = select_experts_from_tasks(["Run a customer study"])
    names = {s.expertise for s in specs}
    # normalized to lowercase
    assert "market research analyst" in names
    # debug should reflect provider
    assert dbg["llm"]["provider"] in {"FakeLLM", None}  # type: ignore[index]
