# backend/app/main.py
# =============================================================================
# What is this file?
# -----------------------------------------------------------------------------
# This is the tiny brain of our backend server (FastAPI).
# It lets you:
#   1) Upload log files and start an analysis job (/analyze)
#   2) Watch job progress (/status/{job_id})
#   3) Get the finished incident summary (/result/{job_id})
#   4) Ask follow-up questions with citations (/ask/{job_id})
#   5) See the exact search text we sent to Pinecone (/debug/query/{job_id})
# It also serves our simple web page at /ui so everything works from one server.
# =============================================================================

from pathlib import Path
from dotenv import load_dotenv

# Load secrets from ../.env (your keys for OpenAI and Pinecone).
# We do this FIRST so all later imports can read those keys.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

import os, uuid, time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Our helpers:
# - retrieve_related_context() talks to Pinecone to find similar cases
# - synthesize_with_llm() and answer_question() talk to the LLM (or use a fallback)
from app.rag.retriever import retrieve_related_context
from app.synthesis import synthesize_with_llm, answer_question

# These classes define the exact shape of JSON our endpoints return.
from .schemas import AnalysisJobStatus, IncidentSummary, TimelineEvent, RootCause


# ---------- Where we keep uploaded files ----------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.abspath(os.path.join(APP_ROOT, "..", "uploads"))
os.makedirs(UPLOAD_ROOT, exist_ok=True)


# ---------- Simple in-memory “database” ----------
# Think of these like two dictionaries on the counter:
# JOBS:   live job tickets while we’re working
# RESULTS:finished write-ups ready to hand back
JOBS: Dict[str, Dict[str, Any]] = {}
RESULTS: Dict[str, IncidentSummary] = {}


# ---------- Start the FastAPI app + allow browser calls ----------
app = FastAPI(title="AgentL3 - Backend", version="0.1.0")

# CORS is wide open so our local web page can talk to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Health check ----------
class HealthResponse(BaseModel):
    ok: bool
    env: Dict[str, bool]

@app.get("/healthz", response_model=HealthResponse)
def healthz():
    """
    Quick "am I alive?" endpoint.
    Also says if your required environment variables are present.
    """
    env = {
        "OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY")),
        "PINECONE_API_KEY_set": bool(os.getenv("PINECONE_API_KEY")),
        "PINECONE_INDEX_set": bool(os.getenv("PINECONE_INDEX")),
    }
    return HealthResponse(ok=True, env=env)


# ---------- Models for the Q&A endpoint (/ask) ----------
class QnARequest(BaseModel):
    question: str  # what the user wants to know

class Citation(BaseModel):
    source: str    # where the snippet came from (e.g., "app.log")
    snippet: str   # the exact line we’re pointing to

class QnAResponse(BaseModel):
    answer: str
    confidence: float
    citations: List[Citation] = []  # show our receipts


# ---------- Save uploaded files to disk ----------
def _save_uploads(job_dir: str, files: List[UploadFile]) -> List[str]:
    """
    Put the uploaded files into uploads/<job_id>/ and return their paths.
    """
    os.makedirs(job_dir, exist_ok=True)
    saved_paths = []
    for f in files:
        dest = os.path.join(job_dir, f.filename)
        with open(dest, "wb") as out:
            out.write(f.file.read())
        saved_paths.append(dest)
    return saved_paths


# ---------- The background pipeline that does the work ----------
def _simulate_pipeline(job_id: str):
    """
    We process a job in 3 kid-friendly steps:

      1) TRIAGE   — skim the logs, keep the most interesting lines
      2) RETRIEVE — ask Pinecone for similar past cases
      3) SYNTHESIZE — let the LLM (or a fallback) write a clean summary

    While we do this, we save two things for later:
      - top_lines: the best log lines (great for citations)
      - query_path: the exact text we searched in Pinecone (for debugging)
    """

    def update(stage: str, progress: int, message: str):
        """
        Update the job ticket so the UI can show a progress bar.
        """
        now = datetime.utcnow()
        job = JOBS[job_id]
        job["stage"] = stage
        job["progress"] = progress
        job["message"] = message
        job["updated_at"] = now

    try:
        # ----- Step 1: TRIAGE (pick the good lines) -----
        update("triage", 20, "Reading files and extracting signals…")
        time.sleep(0.1)

        job_dir = os.path.join(UPLOAD_ROOT, job_id)
        lines: List[str] = []

        # We read text-ish files and keep up to 200 lines per file to stay snappy.
        # Non-empty lines get saved as “signals”.
        if os.path.isdir(job_dir):
            for name in os.listdir(job_dir):
                p = os.path.join(job_dir, name)
                if os.path.isfile(p) and name.lower().endswith((".log", ".txt", ".json")):
                    try:
                        with open(p, "r", errors="ignore") as f:
                            for i, line in enumerate(f):
                                if i >= 200:
                                    break
                                s = line.strip()
                                if s:
                                    lines.append(s)
                    except Exception:
                        # Ignore unreadable files; keep going.
                        pass

        # Make one compact search string from the first 50 “best” lines.
        query_text = " ".join(lines[:50]) or "Database pool timeout after 30s; in_use=50; waiters=12"

        # Save that exact search text to a file so we can show it later in /debug/query.
        q_path = os.path.join(job_dir, "triage_query.txt")
        try:
            with open(q_path, "w") as f:
                f.write(query_text)
            JOBS[job_id]["query_path"] = q_path
            JOBS[job_id]["top_lines"] = lines[:50]  # also cache for /ask
            print(f"[triage] wrote query to {q_path} ({len(query_text)} chars)")
        except Exception as e:
            print(f"[triage] could not write query file: {e}")

        # ----- Step 2: RETRIEVE (ask Pinecone for similar incidents) -----
        update("retrieve", 50, "Retrieving similar past incidents…")
        try:
            related = retrieve_related_context(query_text, top_k=3)
            JOBS[job_id]["related_cases"] = related  # cache for /ask
            print(f"[related_cases] {len(related)} items")
        except Exception as e:
            print(f"[retrieve_error] {e}")
            related = []
        time.sleep(0.1)

        # ----- Step label so the UI looks nice while we compute -----
        update("root_cause", 75, "Evaluating hypotheses…")
        time.sleep(0.05)

        # ----- Step 3: SYNTHESIZE (write the summary) -----
        update("synthesize", 90, "Compiling incident summary…")
        time.sleep(0.05)

        # This tries the LLM if your key is set; otherwise it uses a safe fallback.
        out = synthesize_with_llm(
            query_text=query_text,
            top_lines=JOBS[job_id].get("top_lines") or [],
            related_cases=related,
        )

        # Turn that into our official IncidentSummary object.
        RESULTS[job_id] = IncidentSummary(
            summary=out.get("summary", "Analysis unavailable."),
            confidence=float(out.get("confidence", 0.75)),
            timeline=[TimelineEvent(**t) for t in out.get("timeline", [])],
            immediate_evidence=out.get("immediate_evidence", []),
            root_causes=[RootCause(**rc) for rc in out.get("root_causes", [])],
            next_steps=out.get("next_steps", []),
            related_cases=related,                 # show the RAG matches
            references=out.get("references", []),  # present when LLM was used
        )

        update("done", 100, "Complete")

    except Exception as e:
        # If something unexpected happens, mark the job as error so the UI knows.
        update("error", 100, f"Error: {e}")


# ---------- Routes a user (or the UI) calls ----------
@app.post("/analyze")
async def analyze(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    User uploads logs here.
    We create a job_id, save the files, and start the pipeline in the background.
    The endpoint returns immediately with the job_id.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    JOBS[job_id] = {
        "job_id": job_id,
        "stage": "queued",
        "progress": 0,
        "message": "Queued",
        "created_at": now,
        "updated_at": now,
        "files": [f.filename for f in files],
    }
    job_dir = os.path.join(UPLOAD_ROOT, job_id)
    _ = _save_uploads(job_dir, files)
    background_tasks.add_task(_simulate_pipeline, job_id)
    return {"job_id": job_id}

@app.get("/status/{job_id}", response_model=AnalysisJobStatus)
def status(job_id: str):
    """
    The UI polls this every second or so.
    We return the current stage (queued/triage/retrieve/...), progress %, and messages.
    """
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    j = JOBS[job_id]
    return AnalysisJobStatus(
        job_id=j["job_id"],
        stage=j["stage"],
        progress=j["progress"],
        message=j["message"],
        created_at=j["created_at"],
        updated_at=j["updated_at"],
    )

@app.get("/result/{job_id}", response_model=IncidentSummary)
def result(job_id: str):
    """
    When the job is done, this returns the full incident summary:
    summary, timeline, evidence, likely root causes, next steps, and related cases.
    """
    if job_id not in RESULTS:
        raise HTTPException(status_code=404, detail="Result not ready or job_id not found")
    return RESULTS[job_id]


# ---------- Debug: show the exact Pinecone search text ----------
@app.get("/debug/query/{job_id}")
def debug_query(job_id: str):
    """
    Returns the raw text we searched in Pinecone for that job.
    Super handy to prove what the system actually used.
    """
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    p = j.get("query_path")
    if not p or not os.path.exists(p):
        raise HTTPException(status_code=404, detail="Query text not available for this job")
    return Response(open(p, "r").read(), media_type="text/plain")


# ---------- Q&A: ask a question about this incident ----------
@app.post("/ask/{job_id}", response_model=QnAResponse)
def ask(job_id: str, payload: QnARequest):
    """
    Lets the user ask a follow-up question like:
      “What likely triggered the restarts?”
    We answer using the cached log lines and related cases and include citations.
    """
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Unknown job_id")

    top_lines = j.get("top_lines") or []
    related = j.get("related_cases") or []

    # If for some reason top_lines weren’t cached, fall back to the saved query text.
    if not top_lines:
        qp = j.get("query_path")
        if qp and os.path.exists(qp):
            try:
                with open(qp, "r") as f:
                    txt = f.read().strip()
                if txt:
                    top_lines = [txt[:800]]
            except Exception:
                pass

    out = answer_question(payload.question, top_lines, related)
    return QnAResponse(**out)  # Pydantic turns the dict into the response model


# ---------- Serve the tiny web UI from the same server ----------
from starlette.staticfiles import StaticFiles

# We mount the sibling /frontend folder at /ui.
# This keeps things simple: open http://127.0.0.1:8000/ui to use the app.
app.mount(
    "/ui",
    StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True),
    name="ui",
)