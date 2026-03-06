Author: R. Leung 09/21/25

AgentL3 • Incident Copilot
A tiny incident-response “copilot” for L3/on-call engineers:

Upload production log files
App triages the most “error-y” lines → builds a compact query_text
Uses RAG to fetch related past incidents from Pinecone
Optionally asks an LLM to synthesize a structured incident report
Ask follow-up questions with lightweight, cited answers
Use a simple web UI or Swagger to drive everything
Built to show clean API, Test UI, clear data flow, and pragmatic use of AI where it helps.

To startup uvicorn server:
cd /Users/chiho/ai-lab/AgentL3/backend
source .venv/bin/activate
uvicorn app.main:app --reload

1) Project layout (what’s where)
AGENTL3/ ├─ backend/ │ ├─ app/ │ │ ├─ main.py # FastAPI app: endpoints, orchestration, and /ui mount │ │ ├─ schemas.py # Pydantic models (shapes of JSON the API returns) │ │ ├─ synthesis.py # LLM (or fallback) that produces incident JSON + Q&A │ │ └─ rag/ │ │ ├─ retriever.py # retrieve_related_context() – queries Pinecone │ │ ├─ store.py # Pinecone helpers (index/query plumbing) │ │ └─ embedder.py # OpenAI embedding helpers used by RAG code │ └─ .venv/ # (local virtualenv; ignored from version control) │ ├─ frontend/ │ └─ index.html # Single-file UI: uploads, progress, results, Q&A, debug │ ├─ data/ │ ├─ knowledge/ # Seed “postmortem” markdowns for the RAG index │ └─ samples/ # Demo logs to try in the UI/Swagger (disk_full.log, …) │ ├─ uploads/ # Per-job folders with the raw uploads + triage_query.txt ├─ .env # Environment variables (see note in §3) ├─ .gitignore └─ README.md # (this file)

Start Uvicorn Server (W)

How the system flows (end-to-end)

Upload UI (or Swagger POST /analyze) sends selected files (e.g., *.log, *.txt, *.json). Backend saves them under uploads/<job_id>/.
Triage (backend/app/main.py → _simulate_pipeline()) • Reads the first ~200 lines of each uploaded file • Builds a compact query_text from the top ~50 “signal” lines • Writes that exact text to uploads/<job_id>/triage_query.txt • Caches the lines in memory for later Q&A citations
Retrieve (RAG) (app/rag/retriever.py) • retrieve_related_context(query_text) queries your Pinecone index • Returns the top matching past incidents (filenames + scores)
Synthesize (app/synthesis.py) • If OPENAI_API_KEY is present, calls an LLM to produce a strict JSON: • summary, confidence, timeline, immediate_evidence, root_causes, next_steps, references (short snippets from similar docs) • If the key is missing, a fallback still returns coherent JSON
Store + Serve • The JSON report is cached in memory and returned via GET /result/{job_id} • UI renders it nicely (confidence bars, timeline, related cases, references)
Q&A with citations (POST /ask/{job_id}) • Takes a natural-language question • Uses cached top log lines (+ related cases) to answer • Confidence is a simple rule-based score; citations are raw snippets from those cached lines (so you can see the receipts)
Environment variables

Create a .env file that your app loads.

The current code loads ../.env relative to backend/app/main.py, i.e. backend/.env. If you prefer a repo-root .env, either keep a copy in backend/.env or update the loader path in main.py.

Minimum:

OpenAI (optional but recommended)
OPENAI_API_KEY=sk-... OPENAI_CHAT_MODEL=gpt-4o-mini # default if not set

Pinecone (required for Related Cases)
PINECONE_API_KEY=pcn-... PINECONE_INDEX=agentl3-knowledge # your index name

If Pinecone isn’t seeded with documents from data/knowledge/, the Related cases list will be empty (the rest of the app still works).

Running locally
1) create venv (from the repo root)
cd backend python3 -m venv .venv source .venv/bin/activate pip install -r requirements.txt # (your standard deps list)

2) start the API + serve the UI at /ui
uvicorn app.main:app --reload

3) open one of:
- Web UI http://127.0.0.1:8000/ui
- Swagger (API) http://127.0.0.1:8000/docs
Try with sample logs in data/samples/ (e.g., disk_full.log + thread_pool_exhaustion.log). Watch Job status progress → see a structured summary → ask follow-ups.

API surface (for quick reference) • GET /healthz → { ok, env: {OPENAI_API_KEY_set, PINECONE_API_KEY_set, …} } • POST /analyze → { job_id } multipart form field files supports multiple uploads • GET /status/{job_id} → { stage, progress, message, created_at, updated_at } • GET /result/{job_id} → IncidentSummary JSON (summary, timeline, …, references) • GET /debug/query/{job_id} → raw triage_query.txt (plain text) • POST /ask/{job_id} with { "question": "..." } → { answer, confidence, citations[] }
⸻

The UI (what it does)
frontend/index.html is a single-file app (Tailwind + vanilla JS): • Checks /healthz and shows which keys are configured • Handles file selection (shows count + names) • Calls /analyze, polls /status every ~800ms • Renders /result with confidence bars, timeline, evidence, root causes, steps • Displays Related cases (from Pinecone) and References (LLM snippets) • Sends /ask questions and shows the answer + citations (from your actual logs) • Shows raw triage query (/debug/query) for transparency

Data that lands on disk uploads/<job_id>/ └─ <your_uploaded_logs>.log └─ ... # everything you uploaded └─ triage_query.txt # the exact query text the app searched with This folder is safe to delete after a demo.

Deployment notes (VPS/domain ready) • The backend is a standard ASGI app → run with uvicorn or behind gunicorn+uvicorn, and put nginx in front (TLS, caching, etc.) • The UI is just static assets served by the same app at /ui (simple, same-origin) • Keep your .env out of the repo and set env vars via your process manager (systemd, Docker secrets, etc.)

⸻

Troubleshooting • /ui 404: ensure frontend/ exists; main.py mounts it via Starlette StaticFiles • No “Related cases”: Pinecone not seeded or credentials/index name mismatch • LLM cost concerns: temporarily remove OPENAI_API_KEY → the app uses fallback logic • healthz shows keys missing: check your .env location (see §3) • Swagger “Not Found” for /ui: Swagger lives at /docs; UI is at /ui
⸻

Why this is compelling • Fast feedbackloop: upload → structured summary in seconds • Grounded answers: references and citations point to the exact lines • Explainable: /debug/query shows precisely what was searched • Pragmatic AI: RAG to surface context; LLM for just the synthesis/Q&A layer • Small, readable codebase: easy to extend with Slack/Jira hooks later

# AI Lab – Server Cheat Sheet

## AgentL3
- Backend + UI (FastAPI)
- Port: 8001
- Start:
  ```bash
  cd ~/ai-lab/AgentL3
  uv run uvicorn backend.app.main:app --reload --port 8001


############ EXTENDED NOTES To Add############
# AgentL3 • Incident Copilot (“Log Needler”)

AgentL3 is a tiny but realistic production-support copilot. You upload raw logs, it skims the “spiky” lines, retrieves similar past incidents from a small knowledge base, then writes a clean, executive-ready incident summary with evidence, likely root causes, next steps, and citations. You can also ask follow-up questions (Q&A) against the same job.

> practical AI + RAG for L3/SRE/Operations work: log triage, retrieval-augmented context, and LLM synthesis—wrapped in a simple UI and clean APIs.

---
## What it does (at a glance)

1. **Upload logs** (`.log/.txt/.json`).
2. **Triage**: grab the highest-signal lines (errors/timeouts/back-offs/etc.) and form a compact **query**.
3. **Retrieve**: send that query to a Pinecone index seeded with short **post-mortem notes**; return the most similar incidents.
4. **Synthesize**: use an LLM (or a rules fallback) to write a **summary**, **timeline**, **root causes**, **next steps**, and **references**.
5. **Q&A**: ask natural-language questions about the current job; answers cite the exact lines used.

Why this is useful:
- Faster first-response during incidents.
- Fewer “needle in haystack” hunts.
- Repeatable, auditable summaries with links back to evidence.
- A grounded demo you can show to hiring managers.

---

## Live demo workflow (local)

- Backend runs at `http://127.0.0.1:8000`
- Swagger UI (API explorer): `http://127.0.0.1:8000/docs`
- Minimal web UI: `http://127.0.0.1:8000/ui`

**Typical flow**
1. Open the UI → upload 1–N logs → click **Analyze**.
2. Watch progress: `queued → triage → retrieve → synthesize → done`.
3. View the **Summary, Timeline, Evidence, Root Causes, Next Steps, Related Cases, References**.
4. Click **Show triage query** to see exactly what was embedded for retrieval.
5. Ask a follow-up (“What likely triggered the restarts?”); see the answer with confidence + citations.

---

## How it’s built (key components)

### Backend (FastAPI)
- `backend/app/main.py`
  - **Routes**
    - `POST /analyze` – accepts file uploads, starts a background job, returns `job_id`
    - `GET /status/{job_id}` – progress + stage
    - `GET /result/{job_id}` – structured incident summary (JSON)
    - `POST /ask/{job_id}` – Q&A over the job’s cached signals + retrieved cases
    - `GET /debug/query/{job_id}` – shows the exact query text used for retrieval
  - **In-memory stores**: `JOBS` (status + cache), `RESULTS` (final summary)
  - **Uploads** land in `backend/uploads/<job_id>/` (git-ignored)
  - **UI** is mounted at `/ui` (served with Starlette StaticFiles)

- `backend/app/schemas.py`
  - Pydantic models that define the **shape of JSON** our routes return (e.g., `IncidentSummary`, `TimelineEvent`, etc.). This guarantees consistent responses and auto-documents the API in Swagger.

- `backend/app/rag/retriever.py`
  - `retrieve_related_context(query_text, top_k=3)`:
    - Embeds the query and searches the Pinecone index for the closest post-mortems.
    - Returns a short, human-readable list of “related cases” (e.g., filenames + similarity scores).

- `backend/app/synthesis.py`
  - `synthesize_with_llm(...)`:
    - Sends **high-signal log lines** + **retrieved case names/snippets** to an LLM to produce the final JSON summary.
    - If OpenAI is disabled or unreachable, returns a **coherent rules-based fallback**.
  - `answer_question(...)`:
    - Lightweight Q&A over the job’s cached “top lines” with simple scoring and citations.

### Frontend (vanilla HTML + Tailwind)
- `frontend/index.html`
  - Single-file UI with Tailwind for quick layout.
  - Shows environment health, file upload count + **file names**, progress bar, results, references, and Q&A.
  - Buttons to fetch `/result`, `/ask/{job_id}`, and `/debug/query/{job_id}`.

### Data (for realistic testing)
- `data/knowledge/` – small set of **post-mortems** (Markdown). Example:
  - `postmortem_cache_stampede.md`
  - `postmortem_dns_outage.md`
  - `postmortem_pool_timeout.md`
- `data/samples/` – optional logs to try (e.g., Kubernetes restarts, Kafka consumer lag, NGINX disk full).

### Infra (optional)
- **Uvicorn** for local dev.
- **Caddy** as reverse proxy/TLS in production (we used it to host a portfolio site and can proxy to the backend app).

---

## How the pipeline works (end-to-end)

1. **Upload** (`POST /analyze`): files saved under `backend/uploads/<job_id>/`.
2. **Triage** (background task):
   - Read up to 200 lines per file.
   - Keep the first ~50 “high-signal” lines (error-ish: timeouts, back-offs, exceptions, etc.).
   - Join them into a compact `query_text` and write it to `triage_query.txt` for auditability.
3. **Retrieve**:
   - Embed `query_text` and search Pinecone for similar **post-mortems**.
   - Cache the results in `JOBS[job_id]["related_cases"]`.
4. **Synthesize**:
   - If OpenAI is configured, call the chat model to produce the **summary JSON** (with `references`).
   - Else, return a rules-only fallback summary (no external calls).
5. **Deliver**:
   - Store final `IncidentSummary` in `RESULTS[job_id]`.
   - The UI fetches `/result/{job_id}` and renders the cards.
6. **Q&A**:
   - `POST /ask/{job_id}` answers a free-text question using the cached top lines and related cases.
   - Returns an `answer`, `confidence`, and `citations` (the exact high-signal lines used).

> **Inspectability:** `/debug/query/{job_id}` shows you the precise text that was embedded for retrieval. Helpful to agent
 for troubleshooting.

---

## Value created (why this matters)

- **Speed:** turn noisy logs into an actionable one-pager in seconds.
- **Grounding:** retrieval anchors the narrative in your own post-mortems.
- **Explainability:** every answer has **evidence** (citations + references).
- **Repeatability:** the pipeline is deterministic where it should be (triage rules) and flexible where it helps (LLM synthesis).
- **Portfolio-friendly:** clean code, clear API, simple UI—easy to demo and extend (Slack/Jira integrations later).

---

## Running it locally

### 1) Setup
```bash
cd backend
python -m venv .venv && source .venv/bin/activate          # or: uv venv && source .venv/bin/activate
pip install -r requirements.txt                            # or: uv pip install -r requirements.txt
cp .env.example .env
# fill in:
# OPENAI_API_KEY=...
# PINECONE_API_KEY=...
# PINECONE_INDEX=agentl3-knowledge   # or your chosen index
# OPENAI_CHAT_MODEL=gpt-4o-mini      # default used in code


RAG is optional for a first run. If Pinecone isn’t configured or seeded, the app still works (you’ll just see fewer/empty “related cases”).

2) Seed (optional but recommended)
	•	Put your markdown post-mortems in data/knowledge/.
	•	Use your existing seeding helper, or run a small one-off script to upsert those docs into Pinecone.
	•	Once indexed, /result will start showing meaningful related cases and references.


3) uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
	•	Swagger: http://127.0.0.1:8000/docs
	•	Web UI: http://127.0.0.1:8000/ui

Example artifacts you’ll see
	•	Summary: one paragraph in plain English.
	•	Timeline: 2–10 key events (source + message + time).
	•	Immediate evidence: bullet list of “smoking guns”.
	•	Root causes: hypotheses with confidence (0–1).
	•	Next steps: concrete actions for on-call teams.
	•	Related cases: closest post-mortems (with similarity score).
	•	References: snippets quoted from those post-mortems (LLM path enabled).
	•	Q&A: answers with confidence and citations to the triage lines.

  Configuration & environment
	•	.env lives in backend/ (never commit secrets).
	•	OPENAI_API_KEY – enable LLM path (summary + references + better QA).
	•	PINECONE_API_KEY / PINECONE_INDEX – enable retrieval from your knowledge base.
	•	OPENAI_CHAT_MODEL – defaults to gpt-4o-mini.

Toggles & behavior
	•	If OpenAI is absent, the app returns a sensible rules-based summary.
	•	If Pinecone is absent, you’ll still get a summary, but related cases may be empty.

  AgentL3/
├─ backend/
│  ├─ app/
│  │  ├─ main.py            # FastAPI app: routes, background job, UI mount
│  │  ├─ schemas.py         # Pydantic models (response shapes)
│  │  ├─ rag/
│  │  │  └─ retriever.py    # RAG query -> Pinecone -> related cases
│  │  └─ synthesis.py       # LLM/RULES synthesis + Q&A
│  ├─ uploads/              # per-job uploads + triage_query.txt (gitignored)
│  ├─ .env.example          # sample config
│  └─ requirements.txt
├─ frontend/
│  └─ index.html            # single-file UI (Tailwind + vanilla JS)
└─ data/
   ├─ knowledge/            # markdown post-mortems (seed into Pinecone)
   └─ samples/              # sample logs for testing



Security & privacy notes
	•	Uploads and results are kept in memory and under backend/uploads/ on your machine.
	•	No logs are sent anywhere unless you configure OpenAI/Pinecone.
	•	Do not commit .env or backend/uploads/ to Git.

Roadmap (next enhancements)
	•	Add Slack/Jira connectors for “/analyze” triggers and auto-posted summaries.
	•	Add a datastore for persistent jobs (SQLite/Postgres).
	•	Add settings in the UI (RAG on/off, model choice, log rules).
	•	Expand log parsers (Nginx, Kafka, K8s, DB, app frameworks).

Built with FastAPI, Pydantic, Uvicorn, Tailwind, Pinecone (RAG), and OpenAI (synthesis/Q&A).

