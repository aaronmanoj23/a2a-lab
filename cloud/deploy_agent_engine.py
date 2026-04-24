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

vertexai.init(project=PROJECT_ID, location=REGION, staging_bucket=STAGING)

remote_agent = reasoning_engines.ReasoningEngine.create(
    EchoAgent(),
    display_name="Echo A2A Agent",
    description="A2A Lab — Echo Agent on Agent Engine",
    gcs_dir_name="a2a-staging",
)

print("Deployed! Resource name:", remote_agent.resource_name)
print("Engine ID:", remote_agent.resource_name.split("/")[-1])
