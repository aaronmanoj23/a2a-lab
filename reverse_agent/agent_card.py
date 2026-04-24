# reverse_agent/agent_card.py

AGENT_CARD = {
    "id":          "reverse-agent-v1",
    "name":        "Reverse Agent",
    "version":     "1.0.0",
    "description": "An agent that reverses the word order of any text it receives.",
    "url":         "http://localhost:8001",
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
            "id":          "reverse",
            "name":        "Reverse",
            "description": (
                "Returns the input text with words in reverse order. "
                "e.g. 'Hello World' -> 'World Hello'."
            ),
            "inputModes":  ["text/plain"],
            "outputModes": ["text/plain"]
        }
    ]
}
