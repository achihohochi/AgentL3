from typing import List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class TimelineEvent(BaseModel):
    time: str
    message: str
    source: str

class RootCause(BaseModel):
    cause: str
    confidence: float = Field(ge=0.0, le=1.0)

class Reference(BaseModel):
    source: str      # e.g., "postmortem_pool_timeout.md"
    snippet: str     # short supporting excerpt

class IncidentSummary(BaseModel):
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    timeline: List[TimelineEvent] = []
    immediate_evidence: List[str] = []
    root_causes: List[RootCause] = []
    next_steps: List[str] = []
    related_cases: List[str] = []
    references: List[Reference] = []   # <-- NEW

class AnalysisJobStatus(BaseModel):
    job_id: str
    stage: Literal["queued", "triage", "retrieve", "root_cause", "synthesize", "done", "error"]
    progress: int = Field(ge=0, le=100)
    message: str
    created_at: datetime
    updated_at: datetime

    # ---- NEW for Q&A
class AskRequest(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Reference] = []