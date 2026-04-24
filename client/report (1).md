# A2A Protocol Lab — Report

**Course:** CS4680  
**Assignment:** Building Agent-to-Agent (A2A) Systems in Python  
**Author:** Aaron Manoj  

---

## Section 3 — Request & Response Schema Analysis

### Q1: Why does the request use a client-generated `id` rather than a server-generated one? What problem does this solve in distributed systems?

A client-generated task ID solves the **idempotency problem** in distributed systems. When a client sends a request over an unreliable network, it may time out or receive an error before receiving the server's response. If the server generated the ID, the client would have no way to know whether the request succeeded — retrying would create a duplicate task.

By generating the ID on the client side (typically a UUID), the client already knows the task's identity before sending. If the response is lost and the client retries with the same `id`, a well-implemented server can detect the duplicate and return the already-computed result rather than executing the task a second time. This makes task submission **idempotent**: sending the same request twice has the same effect as sending it once. This is a foundational property in reliable distributed systems (e.g., Stripe payments, AWS SQS exactly-once delivery).

---

### Q2: The `status.state` can be `'working'`. Under what circumstances would a server return this state in a non-streaming call, and how should a client react?

In a **non-streaming** call, a `status.state` of `'working'` means the server accepted the task but has not yet finished processing it at the time of response. This can happen when the agent is performing a long-running operation (e.g., querying an LLM, fetching external data, or running a pipeline) and opts to respond immediately rather than holding the HTTP connection open.

**How a client should react:**

1. **Store the task ID** — the client already has it since it was client-generated.
2. **Poll for completion** — the client should re-query the server (e.g., `GET /tasks/{id}`) at a reasonable interval until `status.state` is `'completed'`, `'failed'`, or `'canceled'`.
3. **Apply backoff** — use exponential backoff to avoid hammering the server while the task runs.
4. **Set a timeout** — stop polling after a maximum duration and surface an error to the user.

In the current Echo Agent implementation, all tasks complete synchronously, so `'working'` will never appear. It becomes relevant for agents backed by slow models or multi-step pipelines.

---

### Q3: What is the purpose of the `sessionId` field? Give a concrete example of two related tasks that should share a session.

The `sessionId` groups multiple related tasks into a **logical conversation or workflow session**. A server can use it to maintain context across requests — for example, remembering what was said earlier in a conversation, accumulating intermediate results, or enforcing ordering within a workflow.

**Concrete example:**

A user is interacting with a document-analysis agent:

- **Task 1:** `sessionId = "session-abc"`, message = `"Summarise the attached quarterly report."`  
  → The agent processes the document and returns a summary.

- **Task 2:** `sessionId = "session-abc"`, message = `"Which risks did you identify?"`  
  → The server uses `sessionId` to retrieve the context from Task 1 and answer the follow-up question correctly, without the client re-sending the full document.

Without `sessionId`, the server would have no way to link Task 2 back to Task 1, and the follow-up question would fail or require the full document to be re-sent.

---

### Q4: The `parts` array supports types `text`, `file`, and `data`. Describe a realistic multi-agent workflow where all three part types appear in a single conversation.

**Scenario: Medical Report Analysis Pipeline**

1. **User → Agent (text + file parts):**  
   A user sends a task with two parts:
   - A `text` part: `"Analyse this lab report and flag any abnormal values."`
   - A `file` part: `{ "url": "https://storage.example.com/reports/lab_report.pdf", "mimeType": "application/pdf" }`  
   The agent downloads and parses the PDF.

2. **Agent → Downstream Analysis Agent (text + data parts):**  
   The first agent routes to a specialised analysis agent, sending:
   - A `text` part: `"Flag values outside reference ranges."`
   - A `data` part: `{ "readings": [{ "test": "HbA1c", "value": 9.2, "unit": "%" }, { "test": "LDL", "value": 185, "unit": "mg/dL" }] }`  
   Structured data is used here because the downstream agent needs machine-readable values, not free text.

3. **Analysis Agent → User (text part):**  
   The response is a `text` part with a human-readable summary: `"Two values are abnormal: HbA1c is elevated at 9.2% (normal < 5.7%) and LDL is high at 185 mg/dL (normal < 100 mg/dL). Recommend follow-up consultation."`

This workflow uses all three part types: `text` for human instructions and output, `file` for raw document upload, and `data` for structured machine-to-machine payloads.

---

## Section 4 — Cloud Run Deployment

### (a) What does `--allow-unauthenticated` do and what are its security implications?

The `--allow-unauthenticated` flag configures the Cloud Run service to **accept HTTP requests without requiring a Google identity token**. By default, Cloud Run enforces IAM authentication — only callers with the `roles/run.invoker` permission can invoke the service.

**Security implications:**

- **Benefit:** Any HTTP client (browser, curl, another agent) can reach the service without needing GCP credentials. This is required for public-facing A2A agents that need to be discoverable by unknown clients.
- **Risk:** The endpoint is fully public on the internet. Anyone who knows (or guesses) the URL can call it, send arbitrary task payloads, and consume compute resources — leading to potential **abuse, denial-of-service, or unexpected costs**.

**Mitigations for production:**

- Add application-level authentication (e.g., API keys, HMAC-signed headers, or OAuth2 bearer tokens verified in middleware).
- Rate-limit requests using Cloud Armor or a Cloud Load Balancer policy.
- For agent-to-agent calls (where both sides are GCP services), use **service account tokens** instead and remove `--allow-unauthenticated`.

For this lab, `--allow-unauthenticated` is acceptable because the Echo Agent handles no sensitive data and the service will be deleted after grading.

---

### (b) How does Cloud Run scale to zero, and what does cold start latency mean for A2A clients?

**Scale to zero:** Cloud Run is a serverless platform. When no requests are arriving, it terminates all running container instances and bills nothing. When a new request arrives, it starts a fresh container from the stored image.

**Cold start latency:** The time between a request arriving and the container being ready to serve it. For a Python/FastAPI container, this is typically **1–4 seconds**, including:
- Container image pull (if not cached in the region)
- Python interpreter startup
- FastAPI application initialisation and route registration

**Impact on A2A clients:**

- The first request after a period of inactivity will experience this delay. The HTTP response will simply arrive later than usual — the A2A protocol is unaffected because it is stateless and the response schema does not change.
- Clients should set a **generous timeout** (the lab uses 30 seconds in `httpx.Client`) to avoid false failures during cold starts.
- For latency-sensitive agents, Cloud Run offers **minimum instances** (`--min-instances=1`) to keep at least one container warm at all times (at additional cost).

---

## Section 5 — Agent Engine Deployment

### (a) Cloud Run vs Agent Engine: operational burden and use-case fit

| Dimension | Cloud Run | Vertex AI Agent Engine |
|-----------|-----------|----------------------|
| **Abstraction level** | Container-level | Agent-framework-level |
| **What you manage** | Dockerfile, HTTP server, routing, uvicorn | Only the Python class with `set_up()` and `query()` |
| **Flexibility** | Any language, any framework | Python only; must fit the query() interface |
| **Observability** | Manual (Cloud Logging, custom metrics) | Built-in agent tracing, LLM call logging |
| **LangChain/LangGraph integration** | Manual setup | Native support |
| **Cold start** | Moderate (container boot) | Higher (heavier managed runtime) |
| **Cost model** | Pay per request/CPU time | Higher per-unit cost; includes managed infra |
| **Best for** | Custom HTTP APIs, non-agent workloads, cost-sensitivity | LLM-backed agents, multi-step reasoning, teams that want zero infra |

**Use-case fit:** Cloud Run is the better choice when you need full control, want to minimise cost, or are building a non-AI HTTP service. Agent Engine is better when the agent uses LangChain/LangGraph, when you want built-in LLM observability, or when the team should not be managing container infrastructure at all.

For the Echo Agent specifically, Cloud Run is the right fit — it is a simple stateless HTTP service with no LLM calls or complex orchestration.

---

### (b) Why does the wrapper use a synchronous `query()` method even though the underlying handler is async?

The Vertex AI Agent Engine runtime calls `query()` **synchronously** — it is not an async-aware framework. If `query()` were declared `async def`, Agent Engine would receive a coroutine object rather than executing it, and the agent would return garbage data.

The solution is to keep `query()` synchronous and use **`asyncio.run()`** to execute the async handler from within it. `asyncio.run()` creates a new event loop, runs the coroutine to completion, and returns the result synchronously — bridging the sync/async boundary cleanly.

This is the standard pattern for calling async code from a sync context in Python. The alternative — making `handle_task` synchronous — would require refactoring the server's handler (which is async because FastAPI and uvicorn are async-native), creating code duplication.

---

## Section 6 — Client-Server Connection Trace

### Logged Output (example run against Cloud Run)

```
============================================================
A2A Demo -- Echo Agent
============================================================
[A2AClient] GET http://localhost:8000/.well-known/agent.json
[A2AClient] Agent Card received: name='Echo Agent', skills=['echo', 'summarise']

Agent Name  : Echo Agent
Agent ID    : echo-agent-v1
Version     : 1.0.0
Description : A simple agent that echoes back any text it receives, and can summarise text on request.

Available Skills (2):
  - [echo] Echo: Returns the user message verbatim.
  - [summarise] Summarise: Returns a one-sentence summary of the provided text. Triggered by prefixing the message with !summarise.

--- Echo Task ---
[A2AClient] POST http://localhost:8000/tasks/send
[A2AClient] Payload (abbreviated): {'id': '15f0dc6e-b092-4ad9-a3e7-f0a2bf7a2c3d', 'sessionId': None, 'message.role': 'user', 'message.parts[0].text': 'Hello from the client!'}
[A2AClient] Response status: completed
Sent    : 'Hello from the client!'
Received: 'Hello from the client!'

--- Summarise Task ---
[A2AClient] POST http://localhost:8000/tasks/send
[A2AClient] Payload (abbreviated): {'id': 'a6470a21-00a6-4dee-81aa-1a7ec0998f0d', 'sessionId': None, 'message.role': 'user', 'message.parts[0].text': '!summarise The quick brown fox jumps over the lazy dog.'}
[A2AClient] Response status: completed
Sent    : '!summarise The quick brown fox...'
Received: 'This is a one-sentence mock summary of the provided text.'

Demo complete.
```

*Note: Output captured from a local run (`http://localhost:8000`). The server was run with `uvicorn server.main:app --reload --port 8000` and the client pointed at the local endpoint. The Cloud Run deployment produces identical output with the service URL substituted.*

---

### UML Sequence Diagram

```
Actor (User)          A2AClient              Cloud Run (A2AServer)       handlers.py
     |                    |                          |                        |
     |  run demo.py       |                          |                        |
     |------------------->|                          |                        |
     |                    |  GET /.well-known/       |                        |
     |                    |  agent.json              |                        |
     |                    |------------------------->|                        |
     |                    |                          |                        |
     |                    |  200 OK {Agent Card}     |                        |
     |                    |<-------------------------|                        |
     |                    |                          |                        |
     |  send_task(text)   |                          |                        |
     |------------------->|                          |                        |
     |                    |  POST /tasks/send        |                        |
     |                    |  {id, message, ...}      |                        |
     |                    |------------------------->|                        |
     |                    |                          |  await handle_task()   |
     |                    |                          |----------------------->|
     |                    |                          |                        |
     |                    |                          |  return result_text    |
     |                    |                          |<-----------------------|
     |                    |  200 OK                  |                        |
     |                    |  {id, status, artifacts} |                        |
     |                    |<-------------------------|                        |
     |                    |                          |                        |
     |  print result      |                          |                        |
     |<-------------------|                          |                        |
```

---

### Retry Safety and Idempotency

**Scenario:** A client sends `POST /tasks/send` but loses the network connection before receiving the response. The task may or may not have been executed.

**Safe retry strategy:**

1. The client already holds the `task_id` (client-generated UUID) before sending.
2. The client retries the same `POST /tasks/send` with the **identical `id`**.
3. A well-implemented A2A server checks if a task with that `id` already exists. If it does, it returns the cached result rather than executing the task again.
4. The client receives the result as if no network failure occurred.

**The A2A field that enables idempotency is `id`** — the client-generated task identifier. Because the client owns the ID, it can retry safely without fear of creating duplicate side effects, as long as the server implements idempotency checks keyed on `id`.

---

## Section 7 — Bonus: Multi-Agent Chain

### (a) How would you add authentication between agents using service account tokens?

In a production multi-agent chain, each agent service should require a valid **Google-signed service account ID token** in the `Authorization: Bearer <token>` header.

**Setup:**

1. Create a dedicated service account for the coordinator: `coordinator@<project>.iam.gserviceaccount.com`.
2. Grant it `roles/run.invoker` on both the EchoAgent and ReverseAgent Cloud Run services.
3. In the coordinator, obtain a token using the Google Auth library:

```python
import google.auth.transport.requests
import google.oauth2.id_token

def get_id_token(audience_url: str) -> str:
    auth_req = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(auth_req, audience_url)
    return token
```

4. Inject the token into each `A2AClient` request by overriding the `httpx.Client` headers:

```python
token = get_id_token(ECHO_AGENT_URL)
self._http = httpx.Client(
    timeout=30,
    headers={"Authorization": f"Bearer {token}"}
)
```

5. Remove `--allow-unauthenticated` from both Cloud Run deployments so Google's IAM layer enforces the token check before the request reaches the container.

This approach means each agent-to-agent call is authenticated at the infrastructure level with no application code changes needed on the server side.

---

### (b) What A2A schema changes would be needed to pass a `sessionId` across the chain?

The `sessionId` field already exists in the A2A task request schema, so **no schema changes are needed**. The coordinator simply generates one `sessionId` UUID at the start of the chain and passes it in every task request it sends, regardless of which agent is the target:

```python
session_id = str(uuid.uuid4())
echo_response    = echo_client.send_task(text,   session_id=session_id)
reverse_response = reverse_client.send_task(text, session_id=session_id)
```

However, for the `sessionId` to be **useful** across agents, two additional conventions would need to be established (these are implementation decisions, not schema changes):

1. **A shared session store** (e.g., Firestore, Redis, or a session management service) that both agents can read from and write to, keyed on `sessionId`.
2. **A convention** that the `sessionId` passed by the coordinator is treated as the chain's session, not as an agent-local session, so downstream agents can retrieve context set by upstream agents.

Without a shared store, `sessionId` is passed through correctly at the protocol level but each agent treats it independently — which is the current behaviour and is sufficient for routing and tracing purposes.
