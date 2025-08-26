from __future__ import annotations

import json

import pytest
from django.test import Client

from agents_core.llm import OpenAILLM, detect_llm


def test_auth_guard_unauthorized_then_authorized(monkeypatch: pytest.MonkeyPatch) -> None:

    # Enable auth and set token
    monkeypatch.setenv("API_ENABLE_AUTH", "1")
    monkeypatch.setenv("API_TOKEN", "secret")
    client = Client()

    # Missing header -> 401
    resp1 = client.get("/api/version")
    assert resp1.status_code == 401

    # Correct token header -> 200
    resp2 = client.get("/api/version", **{"HTTP_X_API_TOKEN": "secret"})
    assert resp2.status_code == 200


def test_rate_limiting_blocks_after_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    from apps.api import views

    # Enable RL with small quota
    monkeypatch.setenv("API_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("API_RATE_LIMIT_PER_MIN", "2")

    # Reset buckets between tests
    views._RL_BUCKETS.clear()  # type: ignore[attr-defined]

    client = Client()
    headers = {"HTTP_X_API_TOKEN": "same-token-for-key"}

    # First two requests succeed
    assert client.get("/api/version", **headers).status_code == 200
    assert client.get("/api/version", **headers).status_code == 200
    # Third should be rate limited
    resp3 = client.get("/api/version", **headers)
    assert resp3.status_code == 429


def test_rate_limit_invalid_value_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from apps.api import views

    monkeypatch.setenv("API_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("API_RATE_LIMIT_PER_MIN", "bad")  # triggers default path
    views._RL_BUCKETS.clear()  # type: ignore[attr-defined]

    client = Client()
    # Should still work and not crash
    assert client.get("/api/version").status_code == 200


def test_memory_history_invalid_limit() -> None:
    client = Client()
    resp = client.get("/api/memory/po/history", {"limit": "bad"})
    assert resp.status_code == 200
    assert resp.json()["limit"] == 20


def test_memory_append_invalid_json() -> None:
    client = Client()
    # Malformed JSON body
    resp = client.post(
        "/api/memory/po/append",
        data="{",
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_memory_append_invalid_serializer() -> None:
    client = Client()
    # Missing required 'item'
    resp = client.post(
        "/api/memory/po/append",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_plan_invalid_json() -> None:
    client = Client()
    resp = client.post("/api/plan", data="{", content_type="application/json")
    assert resp.status_code == 400


def test_plan_invalid_serializer() -> None:
    client = Client()
    resp = client.post("/api/plan", data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 400


def test_plan_debug_flag_includes_debug_block() -> None:
    client = Client()
    resp = client.post(
        "/api/plan?debug=1",
        data=json.dumps({"description": "Build chat"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("tasks"), list)
    assert isinstance(data.get("_debug"), dict)


def test_ac_feedback_invalid_json() -> None:
    client = Client()
    resp = client.post("/api/ac_feedback", data="{", content_type="application/json")
    assert resp.status_code == 400


def test_ac_feedback_invalid_serializer() -> None:
    client = Client()
    resp = client.post("/api/ac_feedback", data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 400


def test_agent_think_invalid_json() -> None:
    client = Client()
    resp = client.post("/api/agent/think", data="{", content_type="application/json")
    assert resp.status_code == 400


def test_agent_think_invalid_serializer() -> None:
    client = Client()
    resp = client.post(
        "/api/agent/think",
        data=json.dumps({"agent": "xx", "goal": "g"}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_agent_think_ac_debug_path() -> None:
    client = Client()
    resp = client.post(
        "/api/agent/think?debug=1",
        data=json.dumps({"agent": "ac", "goal": "Improve process"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("thought"), str)
    assert isinstance(data.get("_debug"), dict)


def test_chat_index_view() -> None:
    client = Client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"AITEAM Chat" in resp.content


def test_short_term_memory_in_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure no REDIS_URL so in-memory path is used
    monkeypatch.delenv("REDIS_URL", raising=False)
    from memory.short_term import ShortTermMemory

    stm = ShortTermMemory()
    stm.append("po", "hello")
    assert stm.history("po", limit=5)[-1] == "hello"


def test_detect_llm_none_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure disabled -> None
    monkeypatch.delenv("ENABLE_LLM", raising=False)
    for k in ("OPENAI_API_KEY", "OLLAMA_HOST", "TRANSFORMERS_MODEL"):
        monkeypatch.delenv(k, raising=False)
    assert detect_llm() is None


def test_detect_llm_openai_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    # Enable and select OpenAI path
    monkeypatch.setenv("ENABLE_LLM", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("TRANSFORMERS_MODEL", raising=False)
    provider = detect_llm()
    assert isinstance(provider, OpenAILLM)
