from __future__ import annotations

from django.test import Client

from memory.short_term import ShortTermMemory


def test_memory_history_endpoint() -> None:
    client = Client()

    stm = ShortTermMemory()
    stm.append("po", "planning: Build chat")
    stm.append("po", "Define acceptance criteria for: Build chat")

    resp = client.get("/api/memory/po/history", {"limit": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "po"
    assert data["limit"] == 2
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 2
    # At least one of our entries should be present
    assert any("Build chat" in it for it in data["items"])
