# client/demo.py

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from client import A2AClient  # noqa: E402

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8000")


def main():
    print("=" * 60)
    print("A2A Demo -- Echo Agent")
    print("=" * 60)

    with A2AClient(AGENT_URL) as client:
        card = client.fetch_agent_card()
        print("\nAgent Name    :", card["name"])
        print("Agent ID      :", card["id"])
        print("Version       :", card["version"])
        print("Description   :", card["description"])

        skills = client.get_skills()
        print("\nAvailable Skills (%d):" % len(skills))
        for skill in skills:
            print("  - [%s] %s: %s" % (skill["id"], skill["name"], skill["description"]))

        print("\n--- Echo Task ---")
        response = client.send_task("Hello from the client!")
        result = client.extract_text(response)
        print("Sent    : 'Hello from the client!'")
        print("Received: '%s'" % result)

        print("\n--- Summarise Task ---")
        msg = "!summarise The quick brown fox jumps over the lazy dog."
        response2 = client.send_task(msg)
        result2 = client.extract_text(response2)
        print("Sent    : '!summarise The quick brown fox...'")
        print("Received: '%s'" % result2)

    print("\nDemo complete.")


if __name__ == "__main__":
    main()
