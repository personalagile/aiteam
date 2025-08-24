from __future__ import annotations

from agents_core.agile_coach import AgileCoachAgent
from agents_core.product_owner import ProductOwnerAgent
from memory.short_term import ShortTermMemory


def test_agents_smoke() -> None:
    mem = ShortTermMemory()
    po = ProductOwnerAgent(name="PO", role="Product Owner", memory=mem)
    ac = AgileCoachAgent(name="AC", role="Agile Coach", memory=mem)

    tasks = po.plan_work("Build chat")
    assert isinstance(tasks, list) and len(tasks) >= 1
    feedback = ac.feedback_on_plan(tasks)
    assert isinstance(feedback, str) and feedback

    msg = ac.schedule_retro()
    assert "retro" in msg.lower()
