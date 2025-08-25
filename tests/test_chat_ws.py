from __future__ import annotations

import asyncio

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator

from aiteam.asgi import application


def test_chat_ws_streaming_messages() -> None:
    async def _run() -> None:
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        connected, _ = await communicator.connect()
        assert connected

        # First system greeting
        sys_msg = await communicator.receive_json_from()
        assert sys_msg.get("type") == "system"

        # Send a user message and expect streaming responses
        await communicator.send_json_to({"message": "Build chat"})

        seen: list[str] = []
        # Read messages until we get final plan and feedback, or timeout
        for _ in range(200):
            try:
                evt = await asyncio.wait_for(communicator.receive_json_from(), timeout=5.0)
            except TimeoutError:
                break
            t = evt.get("type")
            if isinstance(t, str):
                seen.append(t)
            if "po_plan_final" in seen and "ac_feedback" in seen:
                break

        assert "po_plan_start" in seen
        assert "po_plan_final" in seen
        assert "ac_feedback" in seen

        await communicator.disconnect()

    async_to_sync(_run)()
