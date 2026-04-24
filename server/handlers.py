# server/handlers.py

MOCK_SUMMARY = "This is a one-sentence mock summary of the provided text."


async def handle_task(request) -> str:
    """
    Handle an incoming A2A task request.

    Routes to the echo skill by default.
    If the message text starts with '!summarise', routes to the summarise skill
    and returns a mock one-sentence summary.
    """
    text_parts = [p.text for p in request.message.parts if p.type == "text"]
    combined = " ".join(text_parts)

    if combined.startswith("!summarise"):
        return MOCK_SUMMARY

    return combined
