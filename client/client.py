# client/client.py

import httpx
import uuid
from typing import Optional


class A2AClient:
    """Minimal A2A-compliant client."""

    def __init__(self, agent_url: str):
        self.agent_url = agent_url.rstrip("/")
        self._card = None
        self._http = httpx.Client(timeout=30)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """Close the underlying httpx.Client."""
        self._http.close()

    def fetch_agent_card(self) -> dict:
        """Fetch and cache the Agent Card."""
        if self._card is None:
            url = f"{self.agent_url}/.well-known/agent.json"
            print(f"[A2AClient] GET {url}")
            resp = self._http.get(url)
            resp.raise_for_status()
            self._card = resp.json()
            print(f"[A2AClient] Agent Card received: name='{self._card.get('name')}', "
                  f"skills={[s['id'] for s in self._card.get('skills', [])]}")
        return self._card

    def get_skills(self) -> list:
        """Return the skills list from the cached Agent Card."""
        card = self.fetch_agent_card()
        return card.get("skills", [])

    def _build_task(self, text: str, task_id: Optional[str] = None,
                    session_id: Optional[str] = None) -> dict:
        """Build a conformant A2A task payload."""
        return {
            "id":        task_id or str(uuid.uuid4()),
            "sessionId": session_id,
            "message": {
                "role":  "user",
                "parts": [{"type": "text", "text": text}]
            }
        }

    def send_task(self, text: str, **kwargs) -> dict:
        """Send a task and return the parsed response."""
        self.fetch_agent_card()
        payload = self._build_task(text, **kwargs)
        url = f"{self.agent_url}/tasks/send"

        abbreviated = {k: v for k, v in payload.items() if k != "message"}
        abbreviated["message.role"] = payload["message"]["role"]
        abbreviated["message.parts[0].text"] = (
            payload["message"]["parts"][0]["text"][:60] + "..."
            if len(payload["message"]["parts"][0]["text"]) > 60
            else payload["message"]["parts"][0]["text"]
        )
        print(f"[A2AClient] POST {url}")
        print(f"[A2AClient] Payload (abbreviated): {abbreviated}")

        resp = self._http.post(url, json=payload)
        resp.raise_for_status()
        response = resp.json()

        print(f"[A2AClient] Response status: {response.get('status', {}).get('state')}")

        state = response.get("status", {}).get("state")
        if state != "completed":
            raise RuntimeError(
                f"A2A task did not complete. state='{state}', id='{response.get('id')}'"
            )

        return response

    @staticmethod
    def extract_text(response: dict) -> str:
        """Pull the first text or file URL from artifacts."""
        artifacts = response.get("artifacts", [])
        for artifact in artifacts:
            for part in artifact.get("parts", []):
                if part.get("type") == "text":
                    return part["text"]
                if part.get("type") == "file":
                    return part.get("url", "")
        return ""
