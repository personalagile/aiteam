"""WebSocket consumer for the chat UI.

This consumer currently provides a minimal echo behavior and a stub
integration path for routing messages to the ProductOwnerAgent.
"""

from __future__ import annotations

import asyncio

import structlog
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from agents_core.agile_coach import AgileCoachAgent
from agents_core.dynamic_expert import DynamicExpertAgent
from agents_core.product_owner import ProductOwnerAgent
from memory.short_term import ShortTermMemory

logger = structlog.get_logger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Channels JSON consumer for chat messages."""

    async def connect(self) -> None:
        """Accept the connection and greet the client."""
        await self.accept()
        await self.send_json({"type": "system", "message": "Connected to AITEAM chat."})

    async def receive_json(self, content: dict, **kwargs) -> None:  # type: ignore[override]
        """Handle an incoming JSON payload from the client."""
        user_msg = content.get("message")
        logger.info("chat.receive", message=user_msg)
        if not user_msg:
            await self.send_json({"type": "error", "message": "Missing 'message' in payload."})
            return

        # Route to ProductOwnerAgent for planning with progressive updates
        stm = ShortTermMemory()
        # ProductOwnerAgent constructed inline below to reduce locals

        await self.send_json({"type": "po_plan_start", "message": "Planning started."})

        tasks = ProductOwnerAgent(name="po", role="Product Owner", memory=stm).plan_work(
            str(user_msg)
        )

        # Stream individual planning steps
        for idx, task in enumerate(tasks, start=1):
            await asyncio.sleep(0.1)
            await self.send_json({"type": "po_plan_step", "index": idx, "task": task})

        # Final plan
        await self.send_json(
            {
                "type": "po_plan_final",
                "message": f"Plan erstellt: {len(tasks)} Aufgabe(n)",
                "tasks": tasks,
            }
        )
        logger.info("chat.sent_plan", tasks=len(tasks))

        # Agile Coach feedback
        feedback = AgileCoachAgent(name="ac", role="Agile Coach", memory=stm).feedback_on_plan(
            tasks
        )
        await asyncio.sleep(0.1)
        await self.send_json({"type": "ac_feedback", "message": feedback})
        logger.info("chat.sent_ac_feedback")

        # Dynamic Expert selection (now parallelized with streaming updates)
        experts = ["frontend", "backend"]
        await asyncio.sleep(0.1)
        await self.send_json(
            {"type": "expert_update", "message": "Selecting experts...", "experts": []}
        )

        prepared: list[str] = []

        async def _prepare_and_stream(expertise: str) -> None:
            result = DynamicExpertAgent(
                name=f"expert-{expertise}", role="Expert", expertise=expertise, memory=stm
            ).solve(f"Prepare for: {user_msg}")
            prepared.append(expertise)
            await asyncio.sleep(0.05)
            await self.send_json({"type": "expert_update", "expert": expertise, "message": result})

        tasks = [asyncio.create_task(_prepare_and_stream(e)) for e in experts]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)
        await self.send_json(
            {"type": "expert_update", "message": "Experts prepared.", "experts": prepared}
        )
        logger.info("chat.sent_expert_updates", experts=len(prepared))

    async def disconnect(self, code: int) -> None:  # pragma: no cover - event callback
        """Log disconnect events."""
        logger.info("chat.disconnect", code=code)
