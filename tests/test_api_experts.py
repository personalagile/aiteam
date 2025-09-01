from __future__ import annotations

import json

from django.test import Client


def test_experts_run_basic() -> None:
    client = Client()
    resp = client.post(
        "/api/experts/run",
        data=json.dumps({"description": "Build chat UI with Django Channels and Redis"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    # schema checks
    assert isinstance(data.get("tasks"), list)
    assert isinstance(data.get("experts"), list)
    assert isinstance(data.get("results"), dict)
    # tasks are non-empty strings
    assert all(isinstance(t, str) and t.strip() for t in data["tasks"])  # type: ignore[index]
    # experts are non-empty strings
    assert len(data["experts"]) >= 1  # type: ignore[index]
    assert all(isinstance(e, str) and e.strip() for e in data["experts"])  # type: ignore[index]
    # results map contains one entry per expert
    assert set(data["experts"]) == set(data["results"].keys())  # type: ignore[index]
    # each message includes the preparation marker
    for msg in data["results"].values():  # type: ignore[union-attr]
        assert isinstance(msg, str)
        assert "Prepare for:" in msg
        assert "solving" in msg


def test_experts_run_debug() -> None:
    client = Client()
    resp = client.post(
        "/api/experts/run?debug=1",
        data=json.dumps({"description": "Implement API and DB schema"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("_debug"), dict)
    dbg = data["_debug"]  # type: ignore[index]
    # plan and selection blocks should exist
    assert "plan" in dbg and "selection" in dbg


def test_experts_run_invalid_json() -> None:
    client = Client()
    resp = client.post(
        "/api/experts/run",
        data="{",
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_experts_run_invalid_serializer() -> None:
    client = Client()
    resp = client.post(
        "/api/experts/run",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400
