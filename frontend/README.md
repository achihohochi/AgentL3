Author: R. Leung 09/21/25

# AgentL3 • Incident Copilot

A tiny incident-response “copilot” for L3/on-call engineers:

- Upload production **log files**
- App **triages** the most “error-y” lines → builds a compact `query_text`
- Uses **RAG** to fetch **related past incidents** from Pinecone
- Optionally asks an **LLM** to synthesize a structured incident report
- Ask **follow-up questions** with lightweight, **cited** answers
- Use a simple **web UI** or **Swagger** to drive everything

> Built to show clean API, Test UI, clear data flow, and pragmatic use of AI where it helps.

---

## 1) Project layout (what’s where)

AGENTL3/
├─ backend/
│  ├─ app/
│  │  ├─ main.py            # FastAPI app: endpoints, orchestration, and /ui mount
│  │  ├─ schemas.py         # Pydantic models (shapes of JSON the API returns)
│  │  ├─ synthesis.py       # LLM (or fallback) that produces incident JSON + Q&A
│  │  └─ rag/
│  │     ├─ retriever.py    # retrieve_related_context() – queries Pinecone
│  │     ├─ store.py        # Pinecone helpers (index/query plumbing)
│  │     └─ embedder.py     # OpenAI embedding helpers used by RAG code
│  └─ .venv/                # (local virtualenv; ignored from version control)
│
├─ frontend/
│  └─ index.html            # Single-file UI: uploads, progress, results, Q&A, debug
│
├─ data/
│  ├─ knowledge/            # Seed “postmortem” markdowns for the RAG index
│  └─ samples/              # Demo logs to try in the UI/Swagger (disk_full.log, …)
│
├─ uploads/                 # Per-job folders with the raw uploads + triage_query.txt
├─ .env                     # Environment variables (see note in §3)
├─ .gitignore
└─ README.md                # (this file)


Start Uvicorn Server (W)

2) How the system flows (end-to-end)
	1.	Upload
UI (or Swagger POST /analyze) sends selected files (e.g., *.log, *.txt, *.json).
Backend saves them under uploads/<job_id>/.
	2.	Triage (backend/app/main.py → _simulate_pipeline())
	•	Reads the first ~200 lines of each uploaded file
	•	Builds a compact query_text from the top ~50 “signal” lines
	•	Writes that exact text to uploads/<job_id>/triage_query.txt
	•	Caches the lines in memory for later Q&A citations
	3.	Retrieve (RAG) (app/rag/retriever.py)
	•	retrieve_related_context(query_text) queries your Pinecone index
	•	Returns the top matching past incidents (filenames + scores)
	4.	Synthesize (app/synthesis.py)
	•	If OPENAI_API_KEY is present, calls an LLM to produce a strict JSON:
	•	summary, confidence, timeline, immediate_evidence,
root_causes, next_steps, references (short snippets from similar docs)
	•	If the key is missing, a fallback still returns coherent JSON
	5.	Store + Serve
	•	The JSON report is cached in memory and returned via GET /result/{job_id}
	•	UI renders it nicely (confidence bars, timeline, related cases, references)
	6.	Q&A with citations (POST /ask/{job_id})
	•	Takes a natural-language question
	•	Uses cached top log lines (+ related cases) to answer
	•	Confidence is a simple rule-based score; citations are raw snippets from those cached lines (so you can see the receipts)


3) Environment variables

Create a .env file that your app loads.

The current code loads ../.env relative to backend/app/main.py, i.e. backend/.env.
If you prefer a repo-root .env, either keep a copy in backend/.env or update the loader path in main.py.

Minimum:
# OpenAI (optional but recommended)
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini     # default if not set

# Pinecone (required for Related Cases)
PINECONE_API_KEY=pcn-...
PINECONE_INDEX=agentl3-knowledge  # your index name

If Pinecone isn’t seeded with documents from data/knowledge/, the Related cases list will be empty (the rest of the app still works).


4) Running locally
# 1) create venv (from the repo root)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # (your standard deps list)

# 2) start the API + serve the UI at /ui
uvicorn app.main:app --reload

# 3) open one of:
# - Web UI          http://127.0.0.1:8000/ui
# - Swagger (API)   http://127.0.0.1:8000/docs

Try with sample logs in data/samples/ (e.g., disk_full.log + thread_pool_exhaustion.log).
Watch Job status progress → see a structured summary → ask follow-ups.


5) API surface (for quick reference)
	•	GET /healthz → { ok, env: {OPENAI_API_KEY_set, PINECONE_API_KEY_set, …} }
	•	POST /analyze → { job_id }
multipart form field files supports multiple uploads
	•	GET /status/{job_id} → { stage, progress, message, created_at, updated_at }
	•	GET /result/{job_id} → IncidentSummary JSON (summary, timeline, …, references)
	•	GET /debug/query/{job_id} → raw triage_query.txt (plain text)
	•	POST /ask/{job_id} with { "question": "..." } → { answer, confidence, citations[] }

⸻

6) The UI (what it does)

frontend/index.html is a single-file app (Tailwind + vanilla JS):
	•	Checks /healthz and shows which keys are configured
	•	Handles file selection (shows count + names)
	•	Calls /analyze, polls /status every ~800ms
	•	Renders /result with confidence bars, timeline, evidence, root causes, steps
	•	Displays Related cases (from Pinecone) and References (LLM snippets)
	•	Sends /ask questions and shows the answer + citations (from your actual logs)
	•	Shows raw triage query (/debug/query) for transparency



7) Data that lands on disk
uploads/<job_id>/
└─ <your_uploaded_logs>.log
└─ ...                         # everything you uploaded
└─ triage_query.txt            # the exact query text the app searched with
This folder is safe to delete after a demo.


8) Deployment notes (VPS/domain ready)
	•	The backend is a standard ASGI app → run with uvicorn or behind gunicorn+uvicorn, and put nginx in front (TLS, caching, etc.)
	•	The UI is just static assets served by the same app at /ui (simple, same-origin)
	•	Keep your .env out of the repo and set env vars via your process manager (systemd, Docker secrets, etc.)

⸻

9) Troubleshooting
	•	/ui 404: ensure frontend/ exists; main.py mounts it via Starlette StaticFiles
	•	No “Related cases”: Pinecone not seeded or credentials/index name mismatch
	•	LLM cost concerns: temporarily remove OPENAI_API_KEY → the app uses fallback logic
	•	healthz shows keys missing: check your .env location (see §3)
	•	Swagger “Not Found” for /ui: Swagger lives at /docs; UI is at /ui

⸻

10) Why this is compelling
	•	Fast feedback loop: upload → structured summary in seconds
	•	Grounded answers: references and citations point to the exact lines
	•	Explainable: /debug/query shows precisely what was searched
	•	Pragmatic AI: RAG to surface context; LLM for just the synthesis/Q&A layer
	•	Small, readable codebase: easy to extend with Slack/Jira hooks later

