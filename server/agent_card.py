# server/agent_card.py

AGENT_CARD = {
    "id":          "echo-agent-v1",
    "name":        "Echo Agent",
    "version":     "1.0.0",
    "description": (
        "A simple agent that echoes back any text it receives, "
        "and can summarise text on request."
    ),
    "url":         "http://localhost:8000",
    "contact": {
        "email": "aaronmanoj23@gmail.com"
    },
    "capabilities": {
        "streaming": False,
        "pushNotifications": False
    },
    "defaultInputModes":  ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id":          "echo",
            "name":        "Echo",
            "description": "Returns the user message verbatim.",
            "inputModes":  ["text/plain"],
            "outputModes": ["text/plain"]
        },
        {
            "id":          "summarise",
            "name":        "Summarise",
            "description": (
                "Returns a one-sentence summary of the provided text. "
                "Triggered by prefixing the message with !summarise."
            ),
            "inputModes":  ["text/plain"],
            "outputModes": ["text/plain"]
        }
    ]
}


def validate_card(card: dict) -> bool:
    """
    Validate that all required fields are present in an A2A Agent Card.

    Required top-level fields: id, name, version, description, url,
    capabilities, defaultInputModes, defaultOutputModes, skills.
    Each skill must have: id, name, description, inputModes, outputModes.

    Returns True if the card is valid, False if any required field is missing.
    """
    required_top_level = [
        "id", "name", "version", "description", "url",
        "capabilities", "defaultInputModes", "defaultOutputModes", "skills"
    ]
    for field in required_top_level:
        if field not in card:
            return False

    capabilities = card.get("capabilities", {})
    for cap_field in ["streaming", "pushNotifications"]:
        if cap_field not in capabilities:
            return False

    required_skill_fields = ["id", "name", "description", "inputModes", "outputModes"]
    skills = card.get("skills", [])
    if not isinstance(skills, list) or len(skills) == 0:
        return False
    for skill in skills:
        for skill_field in required_skill_fields:
            if skill_field not in skill:
                return False

    return True
