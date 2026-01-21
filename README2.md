# AgentL3 • Incident Copilot

**AgentL3** is an AI-powered incident response assistant designed for L3/on-call engineers and SRE teams. It transforms noisy production logs into actionable, structured incident summaries using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs).

## What It Does

AgentL3 automates the tedious process of log triage and incident analysis:

1. **Upload Production Logs** - Accepts multiple log files (`.log`, `.txt`, `.json`) from production systems
2. **Intelligent Triage** - Automatically extracts the most significant error lines, timeouts, exceptions, and anomalies from logs
3. **Context Retrieval** - Uses RAG to find similar past incidents from a knowledge base of post-mortems stored in Pinecone
4. **Incident Synthesis** - Generates a structured incident report with:
   - Executive summary
   - Timeline of events
   - Immediate evidence (smoking guns)
   - Root cause hypotheses with confidence scores
   - Recommended next steps
   - Related past incidents
   - Citations and references
5. **Interactive Q&A** - Allows follow-up questions with grounded answers that cite exact log lines

## Key Features

### 🔍 **Automated Log Analysis**
- Reads up to 200 lines per log file
- Extracts top 50 high-signal lines (errors, timeouts, back-offs, exceptions)
- Creates a compact query text for semantic search
- Saves triage query for auditability (`triage_query.txt`)

### 🧠 **Retrieval-Augmented Generation (RAG)**
- Embeds log signals using OpenAI's `text-embedding-3-small` model
- Searches Pinecone vector database for similar past incidents
- Returns top 3 most relevant post-mortems with similarity scores
- Knowledge base includes 13+ pre-seeded incident post-mortems covering:
  - Cache stampedes
  - Circuit breaker failures
  - Disk space issues
  - DNS outages
  - Kubernetes OOM kills
  - Kafka consumer lag
  - NGINX upstream timeouts
  - Database pool timeouts
  - PostgreSQL statement timeouts
  - Rate limiting (429 errors)
  - Redis eviction
  - Thread pool exhaustion
  - TLS handshake failures

### 📊 **Structured Incident Reports**
- **Summary**: One-paragraph executive overview
- **Confidence Score**: 0.0-1.0 indicating analysis certainty
- **Timeline**: Chronological sequence of key events with timestamps
- **Immediate Evidence**: Bullet list of critical findings
- **Root Causes**: Hypothesized causes with confidence scores
- **Next Steps**: Concrete actionable recommendations
- **Related Cases**: Similar past incidents from knowledge base
- **References**: Quoted snippets from related post-mortems

### 💬 **Grounded Q&A System**
- Ask natural language questions about the incident
- Answers cite exact log lines used as evidence
- Confidence scores indicate answer reliability
- Citations show source files and snippets

### 🛡️ **Graceful Degradation**
- Works without OpenAI API key (uses rule-based fallback)
- Works without Pinecone (related cases will be empty)
- Error handling ensures pipeline always completes
- Fallback summaries remain useful even without LLM

## Architecture

### Backend (FastAPI)
- **`main.py`**: FastAPI application with REST endpoints
  - `POST /analyze` - Upload logs and start analysis job
  - `GET /status/{job_id}` - Poll job progress
  - `GET /result/{job_id}` - Get final incident summary
  - `POST /ask/{job_id}` - Ask follow-up questions
  - `GET /debug/query/{job_id}` - View exact query text used
  - `GET /healthz` - Health check with environment status
  - `GET /ui` - Serves web UI (static files)
  
- **`schemas.py`**: Pydantic models defining API response shapes
  - `IncidentSummary` - Complete incident report structure
  - `TimelineEvent` - Time-stamped event entries
  - `RootCause` - Cause hypothesis with confidence
  - `Reference` - Citation from knowledge base
  - `AnalysisJobStatus` - Job progress tracking
  - `QnAResponse` - Q&A answer with citations

- **`synthesis.py`**: LLM integration and fallback logic
  - `synthesize_with_llm()` - Generates structured incident summary
  - `answer_question()` - Provides grounded Q&A responses
  - Uses `gpt-4o-mini` by default (configurable)
  - JSON response format for structured output
  - Comprehensive error handling with fallbacks

- **`rag/retriever.py`**: RAG query interface
  - `retrieve_related_context()` - Searches Pinecone for similar incidents
  - Formats results with titles, scores, and takeaways

- **`rag/store.py`**: Pinecone vector database operations
  - `query_similar()` - Vector similarity search
  - `upsert_texts()` - Index new documents
  - `ensure_index()` - Creates index if missing
  - Uses cosine similarity with 1536-dimensional embeddings

- **`rag/embedder.py`**: Text embedding utilities
  - `embed_one()` - Single text embedding
  - `embed_texts()` - Batch embedding
  - Uses OpenAI's embedding API

### Frontend (Vanilla HTML + Tailwind CSS)
- **`index.html`**: Single-file web application
  - File upload interface
  - Real-time progress tracking
  - Results visualization
  - Q&A interface
  - Debug query viewer
  - Environment health indicators

### Data
- **`data/knowledge/`**: Post-mortem markdown files (seed for Pinecone)
- **`data/log_samples/`**: Sample log files for testing
- **`uploads/{job_id}/`**: Per-job uploads and triage queries (git-ignored)

## How It Works (End-to-End Flow)

1. **Upload Phase**
   - User uploads log files via web UI or API
   - Files saved to `uploads/{job_id}/`
   - Job created with status "queued"

2. **Triage Phase** (20% progress)
   - Reads first 200 lines from each log file
   - Extracts non-empty lines as "signals"
   - Takes top 50 lines and joins into query text
   - Saves query to `triage_query.txt` for auditability
   - Caches top lines for later Q&A

3. **Retrieve Phase** (50% progress)
   - Embeds query text using OpenAI embeddings
   - Searches Pinecone index for similar post-mortems
   - Returns top 3 matches with similarity scores
   - Caches results for synthesis and Q&A

4. **Root Cause Analysis** (75% progress)
   - Placeholder stage for UI feedback

5. **Synthesize Phase** (90% progress)
   - If OpenAI API key present:
     - Sends top log lines + related cases to LLM
     - LLM generates structured JSON summary
     - Includes references from knowledge base
   - If OpenAI unavailable:
     - Uses rule-based fallback
     - Still produces useful summary structure

6. **Complete** (100% progress)
   - Final `IncidentSummary` stored in memory
   - Available via `GET /result/{job_id}`
   - UI renders structured report

7. **Q&A Phase** (on-demand)
   - User asks natural language question
   - System uses cached top lines + related cases
   - LLM generates answer with citations
   - Returns answer, confidence, and source citations

## Technology Stack

- **Backend Framework**: FastAPI (Python)
- **LLM Provider**: OpenAI (GPT-4o-mini)
- **Vector Database**: Pinecone
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Web Server**: Uvicorn (ASGI)
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **Data Validation**: Pydantic
- **File Handling**: Python multipart uploads

## Environment Configuration

Required environment variables (in `backend/.env`):

```bash
# OpenAI (optional but recommended)
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini  # default if not set
EMBED_MODEL=text-embedding-3-small  # default if not set

# Pinecone (required for RAG)
PINECONE_API_KEY=pcn-...
PINECONE_INDEX=agentl3-knowledge  # your index name
PINECONE_CLOUD=aws  # optional, default: aws
PINECONE_REGION=us-east-1  # optional, default: us-east-1
```

## Use Cases

- **On-Call Engineers**: Quickly triage production incidents during alerts
- **SRE Teams**: Generate post-mortem drafts from incident logs
- **DevOps**: Analyze system failures and identify patterns
- **Incident Response**: Get structured summaries for stakeholder communication
- **Knowledge Management**: Learn from past incidents via RAG retrieval

## Value Proposition

- **Speed**: Transform noisy logs into actionable summaries in seconds
- **Grounding**: Answers anchored in your own post-mortem knowledge base
- **Explainability**: Every answer includes citations and evidence
- **Repeatability**: Deterministic triage rules + flexible LLM synthesis
- **Auditability**: Query text saved for transparency and debugging
- **Portfolio-Ready**: Clean codebase, clear API, simple UI - easy to demo and extend

## Limitations & Considerations

- **In-Memory Storage**: Jobs and results stored in memory (not persistent)
- **File Limits**: Processes up to 200 lines per file for performance
- **Token Costs**: LLM calls incur OpenAI API costs
- **Vector Database**: Requires Pinecone account and seeded knowledge base
- **Single Server**: Not designed for horizontal scaling (stateless design allows it)

## Future Enhancements

Potential improvements mentioned in codebase:
- Slack/Jira integrations for automated incident posting
- Persistent storage (SQLite/Postgres) for job history
- Configurable settings in UI (RAG on/off, model selection)
- Expanded log parsers (Nginx, Kafka, Kubernetes, database-specific)
- Multi-user support with authentication
- Export reports to PDF/Markdown

## Getting Started

See the main `README.md` for detailed setup instructions, including:
- Virtual environment setup
- Dependency installation
- Environment configuration
- Pinecone index seeding
- Running the server
- Using the web UI

---

**Built with**: FastAPI, Pydantic, Uvicorn, Tailwind CSS, Pinecone (RAG), OpenAI (LLM synthesis)

**Author**: R. Leung (09/21/25)

**Version**: 0.1.0
