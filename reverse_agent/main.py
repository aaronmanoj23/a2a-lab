# reverse_agent/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from agent_card import AGENT_CARD
from handlers import handle_task

app = FastAPI(title="Reverse A2A Agent")


@app.get("/.well-known/agent.json")
async def get_agent_card():
    return AGENT_CARD


@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": AGENT_CARD["id"]}


class TextPart(BaseModel):
    type: str = "text"
    text: str


class FilePart(BaseModel):
    type: str = "file"
    url: str
    mimeType: str


class Message(BaseModel):
    role: str
    parts: list[TextPart | FilePart]


class TaskRequest(BaseModel):
    id: str
    sessionId: Optional[str] = None
    message: Message
    metadata: Optional[dict[str, Any]] = None


@app.post("/tasks/send")
async def send_task(request: TaskRequest):
    if not request.message.parts:
        raise HTTPException(
            status_code=400,
            detail="message.parts must contain at least one part."
        )

    result_text = await handle_task(request)

    return {
        "id":     request.id,
        "status": {"state": "completed", "message": None},
        "artifacts": [
            {
                "index": 0,
                "name":  "result",
                "parts": [{"type": "text", "text": result_text}]
            }
        ]
    }
