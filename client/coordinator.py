# client/coordinator.py

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from client import A2AClient  # noqa: E402

ECHO_AGENT_URL = os.environ.get("ECHO_AGENT_URL", "http://localhost:8000")
REVERSE_AGENT_URL = os.environ.get("REVERSE_AGENT_URL", "http://localhost:8001")

INPUT_TEXT = "Hello World this is a multi-agent A2A chain"


def main():
    print("=" * 60)
    print("Multi-Agent Coordinator: Echo -> Reverse")
    print("=" * 60)
    print("\nInput text : '%s'" % INPUT_TEXT)

    with A2AClient(ECHO_AGENT_URL) as echo_client, \
         A2AClient(REVERSE_AGENT_URL) as reverse_client:

        echo_card = echo_client.fetch_agent_card()
        echo_skills = [s["id"] for s in echo_client.get_skills()]
        print("\n[1] Connected to EchoAgent    : '%s' @ %s" % (
            echo_card["name"], ECHO_AGENT_URL))
        print("    Skills: %s" % echo_skills)

        reverse_card = reverse_client.fetch_agent_card()
        reverse_skills = [s["id"] for s in reverse_client.get_skills()]
        print("[2] Connected to ReverseAgent : '%s' @ %s" % (
            reverse_card["name"], REVERSE_AGENT_URL))
        print("    Skills: %s" % reverse_skills)

        print("\n[3] Sending to EchoAgent...")
        echo_response = echo_client.send_task(INPUT_TEXT)
        echo_result = echo_client.extract_text(echo_response)
        print("    Echo result : '%s'" % echo_result)

        print("\n[4] Sending EchoAgent output to ReverseAgent...")
        reverse_response = reverse_client.send_task(echo_result)
        final_result = reverse_client.extract_text(reverse_response)
        print("    Final result: '%s'" % final_result)

    print("\n" + "=" * 60)
    print("Input : '%s'" % INPUT_TEXT)
    print("Output: '%s'" % final_result)
    print("=" * 60)


if __name__ == "__main__":
    main()
