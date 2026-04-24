# A2A Lab — Echo & Reverse Agent

**CS4680 | Building Agent-to-Agent (A2A) Systems in Python**

---

## Project Structure

```
a2a-lab/
├── server/
│   ├── main.py                  # A2A Server (FastAPI)
│   ├── agent_card.py            # Agent Card definition + validate_card()
│   ├── handlers.py              # Task handler logic (echo + summarise)
│   ├── agent_engine_wrapper.py  # Vertex AI Agent Engine wrapper
│   ├── Dockerfile
│   └── requirements.txt
├── reverse_agent/
│   ├── main.py                  # Reverse A2A Agent (FastAPI)
│   ├── agent_card.py            # Reverse Agent Card
│   ├── handlers.py              # Word-reversal handler
│   ├── Dockerfile
│   └── requirements.txt
├── client/
│   ├── client.py                # A2AClient class
│   ├── demo.py                  # End-to-end demo (Echo Agent)
│   └── coordinator.py           # Bonus: multi-agent chain coordinator
├── cloud/
│   ├── deploy_cloud_run.sh             # Deploy Echo Agent to Cloud Run
│   ├── deploy_reverse_agent_cloud_run.sh  # Deploy Reverse Agent to Cloud Run
│   └── deploy_agent_engine.py          # Deploy Echo Agent to Vertex AI Agent Engine
├── report.md                    # Written answers (Sections 3–7)
└── README.md
```

---

## Environment Setup

### Prerequisites

- Python 3.10+
- Docker Desktop
- Google Cloud CLI (`gcloud`) — run `gcloud init` and `gcloud auth login`
- A GCP project with billing enabled
- APIs enabled: Cloud Run, Artifact Registry, Vertex AI

### Python Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install fastapi uvicorn httpx pydantic google-cloud-aiplatform google-auth requests
```

---

## Part 1 & 2 — Run Locally

### Start the Echo Agent Server

```bash
cd server
uvicorn main:app --reload --port 8000
```

### Verify with curl

```bash
# Agent Card
curl http://localhost:8000/.well-known/agent.json

# Health check
curl http://localhost:8000/health

# Send a task (echo)
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t1","message":{"role":"user","parts":[{"type":"text","text":"Hello A2A"}]}}'

# Send a summarise task
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t2","message":{"role":"user","parts":[{"type":"text","text":"!summarise The quick brown fox jumps over the lazy dog."}]}}'
```

### Run the Client Demo

```bash
# In a second terminal (server must be running)
python client/demo.py
```

### Start the Reverse Agent (Bonus)

```bash
cd reverse_agent
uvicorn main:app --reload --port 8001
```

### Run the Multi-Agent Coordinator (Bonus)

```bash
# Both servers must be running (Echo on 8000, Reverse on 8001)
python client/coordinator.py
```

---

## Part 4 — Cloud Run Deployment

1. Edit `cloud/deploy_cloud_run.sh` and replace `your-gcp-project-id` with your real project ID.

2. Run the script:
   ```bash
   bash cloud/deploy_cloud_run.sh
   ```

3. Note the **Service URL** printed at the end.

4. Update `AGENT_CARD["url"]` in `server/agent_card.py` to the Cloud Run URL, then redeploy.

5. Verify from the cloud:
   ```bash
   curl https://<SERVICE_URL>/.well-known/agent.json
   ```

6. Run the demo against the cloud:
   ```bash
   AGENT_URL=https://<SERVICE_URL> python client/demo.py
   ```

**Cloud Run Service URL:** https://echo-a2a-agent-tyvibunxva-uc.a.run.app  
**Agent Engine ID:** `6643856735196938240`

---

## Part 5 — Vertex AI Agent Engine Deployment

1. Create the GCS staging bucket:
   ```bash
   gsutil mb -l us-central1 gs://<your-project-id>-a2a-staging
   ```

2. Edit `cloud/deploy_agent_engine.py` and replace `your-gcp-project-id`.

3. Run the deployment:
   ```bash
   python cloud/deploy_agent_engine.py
   ```

4. Note the **Engine ID** printed at the end.

5. Test the deployed agent:
   ```python
   from vertexai.preview import reasoning_engines
   agent = reasoning_engines.ReasoningEngine(
       'projects/<PROJECT>/locations/us-central1/reasoningEngines/<ENGINE_ID>'
   )
   response = agent.query(message_text='Hello from Agent Engine!')
   print(response)
   ```

---

## Bonus — Deploy Reverse Agent to Cloud Run

```bash
bash cloud/deploy_reverse_agent_cloud_run.sh
```

Then run the coordinator against both cloud deployments:

```bash
ECHO_AGENT_URL=https://<ECHO_SERVICE_URL> \
REVERSE_AGENT_URL=https://<REVERSE_SERVICE_URL> \
python client/coordinator.py
```

---

## Cleanup (Avoid Charges)

```bash
gcloud run services delete echo-a2a-agent    --region=us-central1
gcloud run services delete reverse-a2a-agent --region=us-central1
```

---

## Code Style

All Python files pass `flake8` with no errors:
```bash
pip install flake8
flake8 server/ client/ reverse_agent/ cloud/
```
