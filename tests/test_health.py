from __future__ import annotations

from django.test import Client


def test_health_endpoint() -> None:
    client = Client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
