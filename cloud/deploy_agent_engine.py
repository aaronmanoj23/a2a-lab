# cloud/deploy_agent_engine.py

import vertexai
from vertexai.preview import reasoning_engines
import sys
import os

PROJECT_ID='project-be2f04a0-77d8-47ca-abf'
REGION     = "us-central1"
STAGING    = f"gs://{PROJECT_ID}-a2a-staging"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from agent_engine_wrapper import EchoAgent

vertexai.init(project=PROJECT_ID, location=REGION)

remote_agent = reasoning_engines.ReasoningEngine.create(
    EchoAgent(),
    requirements=[
        "fastapi==0.111.0",
        "uvicorn==0.29.0",
        "pydantic==2.7.0",
    ],
    display_name="Echo A2A Agent",
    description="A2A Lab — Echo Agent on Agent Engine",
    gcs_dir_name=STAGING,
)

print("Deployed! Resource name:", remote_agent.resource_name)
print("Engine ID:", remote_agent.resource_name.split("/")[-1])
