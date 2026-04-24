# reverse_agent/handlers.py


async def handle_task(request) -> str:
    """
    Handle an incoming A2A task request for the Reverse Agent.

    Collects all text parts and returns them with word order reversed.
    e.g. 'Hello World' -> 'World Hello'.
    """
    text_parts = [p.text for p in request.message.parts if p.type == "text"]
    combined = " ".join(text_parts)
    words = combined.split()
    return " ".join(reversed(words))
