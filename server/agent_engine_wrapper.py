# server/agent_engine_wrapper.py
import uuid


class EchoAgent:
    """Agent Engine wrapper for the Echo A2A Agent."""

    def set_up(self):
        """Called once when the Agent Engine container starts."""
        print("EchoAgent.set_up() called")

    def query(self, *, task_id: str = None, message_text: str) -> dict:
        """Entry point called by Agent Engine for each request."""
        from types import SimpleNamespace

        fake_request = SimpleNamespace(
            id=task_id or str(uuid.uuid4()),
            message=SimpleNamespace(
                role="user",
                parts=[SimpleNamespace(type="text", text=message_text)]
            )
        )

        text_parts = [p.text for p in fake_request.message.parts if p.type == "text"]
        combined = " ".join(text_parts)

        if combined.startswith("!summarise"):
            result_text = "This is a one-sentence mock summary of the provided text."
        else:
            result_text = combined

        return {
            "id": fake_request.id,
            "status": {"state": "completed", "message": None},
            "artifacts": [{"parts": [{"type": "text", "text": result_text}]}]
        }
