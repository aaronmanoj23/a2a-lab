# server/agent_engine_wrapper.py

import uuid
from handlers import handle_task


class EchoAgent:
    """Agent Engine wrapper for the Echo A2A Agent."""

    def set_up(self):
        """Called once when the Agent Engine container starts."""
        print("EchoAgent.set_up() called")

    def query(self, *, task_id: str = None, message_text: str) -> dict:
        """
        Entry point called by Agent Engine for each request.

        Uses asyncio.run() to bridge the sync/async boundary since
        Agent Engine's query() interface is synchronous.
        """
        from types import SimpleNamespace
        import asyncio

        fake_request = SimpleNamespace(
            id=task_id or str(uuid.uuid4()),
            message=SimpleNamespace(
                role="user",
                parts=[SimpleNamespace(type="text", text=message_text)]
            )
        )

        result_text = asyncio.run(handle_task(fake_request))

        return {
            "id":       fake_request.id,
            "status":   {"state": "completed", "message": None},
            "artifacts": [
                {"parts": [{"type": "text", "text": result_text}]}
            ]
        }
