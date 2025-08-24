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
    assert data.get("count") == len(data["tasks"]) == 2
    assert any("Build chat" in t for t in data["tasks"])  # echo of description


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
