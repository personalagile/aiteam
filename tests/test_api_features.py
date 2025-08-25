from __future__ import annotations

import json

from django.test import Client


def test_plan_endpoint_returns_tasks() -> None:
    client = Client()
    resp = client.post(
        "/api/plan",
        data=json.dumps({"description": "Build chat"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("tasks"), list)
    assert data.get("count") == len(data["tasks"])  # count must match
    assert len(data["tasks"]) >= 1  # at least one task
    assert all(isinstance(t, str) and t.strip() for t in data["tasks"])  # non-empty strings


def test_ac_feedback_endpoint_returns_feedback() -> None:
    client = Client()
    resp = client.post(
        "/api/ac_feedback",
        data=json.dumps({"tasks": ["Define acceptance criteria for: Build chat"]}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("feedback"), str)
    assert data["feedback"].strip() != ""


def test_retro_run_endpoint() -> None:
    client = Client()
    resp = client.post("/api/retro/run", data="{}", content_type="application/json")
    assert resp.status_code == 202
    data = resp.json()
    assert data.get("accepted") is True
    assert isinstance(data.get("scheduled"), bool)


def test_version_endpoint() -> None:
    client = Client()
    resp = client.get("/api/version")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("version"), str)
    assert data["version"]


def test_memory_append_and_history_roundtrip() -> None:
    client = Client()
    agent = "po"
    item = "test memory append"
    resp = client.post(
        f"/api/memory/{agent}/append",
        data=json.dumps({"item": item}),
        content_type="application/json",
    )
    assert resp.status_code == 201
    # Verify via history
    resp2 = client.get(f"/api/memory/{agent}/history", {"limit": 5})
    assert resp2.status_code == 200
    data = resp2.json()
    assert any(item in s for s in data.get("items", []))


def test_agent_think_endpoint() -> None:
    client = Client()
    resp = client.post(
        "/api/agent/think",
        data=json.dumps({"agent": "po", "goal": "Ship MVP"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("thought"), str)
    assert data["thought"].strip() != ""
