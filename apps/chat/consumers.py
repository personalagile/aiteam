"""WebSocket consumer for the chat UI.

Streams Product Owner planning steps, Agile Coach feedback, and dynamic expert
selection/preparation updates. Emits JSON events: ``po_plan_start``,
``po_plan_step``, ``po_plan_final``, ``ac_feedback``, and ``expert_update``.
The initial ``expert_update`` may include a ``_debug`` payload with LLM/
heuristic details used for expert selection.
"""

from __future__ import annotations

import asyncio

import structlog
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from agents_core.agile_coach import AgileCoachAgent
from agents_core.dynamic_expert import (
    DynamicExpertAgent,
    create_agents,
    select_experts_from_tasks,
)
from agents_core.product_owner import ProductOwnerAgent
from memory.short_term import ShortTermMemory

logger = structlog.get_logger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Channels JSON consumer for chat messages."""

    async def connect(self) -> None:
        """Accept the connection and greet the client."""
        await self.accept()
        await self.send_json({"type": "system", "message": "Connected to AITEAM chat."})

    async def _plan_and_stream(self, stm: ShortTermMemory, user_msg: str) -> list[str]:
        """Plan with `ProductOwnerAgent` and stream progress and final result."""
        await self.send_json({"type": "po_plan_start", "message": "Planning started."})
        po_tasks: list[str] = ProductOwnerAgent(
            name="po", role="Product Owner", memory=stm
        ).plan_work(str(user_msg))
        for idx, task in enumerate(po_tasks, start=1):
            await asyncio.sleep(0.1)
            await self.send_json({"type": "po_plan_step", "index": idx, "task": task})
        await self.send_json(
            {
                "type": "po_plan_final",
                "message": f"Plan erstellt: {len(po_tasks)} Aufgabe(n)",
                "tasks": po_tasks,
            }
        )
        logger.info("chat.sent_plan", tasks=len(po_tasks))
        return po_tasks

    async def _select_and_prepare_experts(
        self, stm: ShortTermMemory, po_tasks: list[str], user_msg: str
    ) -> None:
        """Select experts and stream preparation concurrently."""
        await asyncio.sleep(0.1)
        specs, dbg = select_experts_from_tasks(po_tasks)
        expert_names = [s.expertise for s in specs]
        await self.send_json(
            {
                "type": "expert_update",
                "message": "Selecting experts...",
                "experts": expert_names,
                "_debug": dbg,
            }
        )
        agents: list[DynamicExpertAgent] = create_agents(specs, memory=stm)
        prepared: list[str] = []

        async def _prepare_and_stream(agent: DynamicExpertAgent) -> None:
            result = agent.solve(f"Prepare for: {user_msg}")
            prepared.append(agent.expertise)
            await asyncio.sleep(0.05)
            await self.send_json(
                {"type": "expert_update", "expert": agent.expertise, "message": result}
            )

        jobs = [asyncio.create_task(_prepare_and_stream(a)) for a in agents]
        await asyncio.gather(*jobs)
        await asyncio.sleep(0.1)
        await self.send_json(
            {"type": "expert_update", "message": "Experts prepared.", "experts": prepared}
        )
        logger.info("chat.sent_expert_updates", experts=len(prepared))

    async def receive_json(self, content: dict, **kwargs) -> None:  # type: ignore[override]
        """Handle an incoming JSON payload from the client."""
        user_msg = content.get("message")
        logger.info("chat.receive", message=user_msg)
        if not user_msg:
            await self.send_json({"type": "error", "message": "Missing 'message' in payload."})
            return

        stm = ShortTermMemory()
        po_tasks = await self._plan_and_stream(stm, str(user_msg))
        feedback = AgileCoachAgent(name="ac", role="Agile Coach", memory=stm).feedback_on_plan(
            po_tasks
        )
        await asyncio.sleep(0.1)
        await self.send_json({"type": "ac_feedback", "message": feedback})
        logger.info("chat.sent_ac_feedback")
        await self._select_and_prepare_experts(stm, po_tasks, str(user_msg))

    async def disconnect(self, code: int) -> None:  # pragma: no cover - event callback
        """Log disconnect events."""
        logger.info("chat.disconnect", code=code)
