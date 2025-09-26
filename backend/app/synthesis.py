# backend/app/synthesis.py

import os, json
from typing import List, Dict, Any
from openai import OpenAI

# --- Small helpers ------------------------------------------------------------

def _safe_list(x, fallback=None):
    if isinstance(x, list):
        return x
    return fallback if fallback is not None else []

def _coerce_timeline(items):
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        time = str(it.get("time") or "-")
        msg = str(it.get("message") or "")
        src = str(it.get("source") or "analysis")
        if msg:
            out.append({"time": time, "message": msg, "source": src})
    return out[:12]

def _coerce_root_causes(items):
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        cause = str(it.get("cause") or "")
        conf = it.get("confidence", 0.7)
        try:
            conf = float(conf)
        except:
            conf = 0.7
        if cause:
            out.append({"cause": cause, "confidence": max(0.0, min(1.0, conf))})
    return out[:6]

def _coerce_refs(items):
    """Normalize list of {source, snippet} dicts."""
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        src = str(it.get("source") or "retrieved_case")
        snip = str(it.get("snippet") or "")
        if snip:
            out.append({"source": src, "snippet": snip})
    return out[:10]

def _clip_lines(lines: List[str], n: int = 50) -> List[str]:
    """Keep only the first N non-empty lines to control token cost."""
    out = []
    for s in lines:
        s = (s or "").strip()
        if not s:
            continue
        out.append(s)
        if len(out) >= n:
            break
    return out

# --- Incident synthesis (summary/root_causes/next_steps/references) -----------

def synthesize_with_llm(query_text: str, top_lines: List[str], related_cases: List[str]) -> Dict[str, Any]:
    """
    Ask the LLM to write the incident summary using high-signal log lines
    and the retrieved case names, and to emit references (doc + snippet).
    Returns a dict with keys expected by IncidentSummary (minus related_cases).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    # If key is missing, return a safe fallback so the pipeline completes.
    if not api_key:
        tl = [{"time": "-", "message": s, "source": "analysis"} for s in _clip_lines(top_lines)]
        return {
            "summary": "Auto-summary (LLM disabled): based on log evidence and related cases.",
            "confidence": 0.5,
            "timeline": tl,
            "immediate_evidence": _clip_lines(top_lines, n=12),
            "root_causes": [{"cause": "Likely issue inferred from logs", "confidence": 0.4}],
            "next_steps": ["Review logs and related cases; LLM synthesizer is disabled."],
            "references": [],
        }

    client = OpenAI(api_key=api_key)

    sys = (
        "You are a senior SRE. Given high-signal log lines and similar past incidents, "
        "produce a concise, actionable incident analysis. Return strict JSON with keys: "
        '{"summary": string, "confidence": number, '
        '"timeline": [{"time": string,"message": string,"source": string}], '
        '"immediate_evidence": [string], '
        '"root_causes": [{"cause": string,"confidence": number}], '
        '"next_steps": [string], '
        '"references": [{"source": string,"snippet": string}] }'
    )

    top_lines_text = "\n".join(_clip_lines(top_lines, 50))
    related_text = "\n".join(f"- {rc}" for rc in (related_cases or [])[:5])

    user = (
        f"LOG SIGNALS (top lines):\n{top_lines_text}\n\n"
        f"RETRIEVED RELATED CASES:\n{related_text}\n\n"
        "Return ONLY the JSON object."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        # On any API/parse error, return a minimal-but-valid fallback.
        tl = [{"time": "-", "message": s, "source": "analysis"} for s in _clip_lines(top_lines)]
        return {
            "summary": f"Analysis unavailable (synthesis error).",
            "confidence": 0.5,
            "timeline": tl,
            "immediate_evidence": _clip_lines(top_lines, n=12),
            "root_causes": [{"cause": "Unknown (synthesis error)", "confidence": 0.3}],
            "next_steps": ["Retry synthesis later; check logs and related cases."],
            "references": [],
        }

    return {
        "summary": data.get("summary", "Analysis unavailable."),
        "confidence": float(data.get("confidence", 0.75)),
        "timeline": _coerce_timeline(_safe_list(data.get("timeline"), [])),
        "immediate_evidence": _safe_list(data.get("immediate_evidence"), [])[:12],
        "root_causes": _coerce_root_causes(_safe_list(data.get("root_causes"), [])),
        "next_steps": _safe_list(data.get("next_steps"), [])[:10],
        "references": _coerce_refs(_safe_list(data.get("references"), [])),
    }

# --- Grounded Q&A (answers with citations) ------------------------------------

def answer_question(question: str, top_lines: List[str], related_cases: List[str]) -> Dict[str, Any]:
    """
    Grounded Q&A: answer using ONLY the provided log lines and retrieved cases.
    Returns: { "answer": str, "confidence": float, "citations": [ {source, snippet}, ... ] }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    # If key is missing, provide a graceful response.
    if not api_key:
        return {
            "answer": "LLM is disabled; cannot answer the question.",
            "confidence": 0.0,
            "citations": [],
        }

    client = OpenAI(api_key=api_key)

    logs_text = "\n".join(_clip_lines(top_lines, 50))
    related_text = "\n".join(f"- {rc}" for rc in (related_cases or [])[:5])

    system = (
        "You are an SRE assistant. Answer the user's question using ONLY the provided log lines "
        "and the retrieved past cases. Be concise (<=4 sentences). If there's not enough evidence, "
        'say so. Return strict JSON with keys: '
        '{"answer": string, "confidence": number, "citations": [{"source": string,"snippet": string}]}. '
        "For citations, use the source names provided (e.g., 'app.log' or postmortem filenames) and short snippets."
    )
    user = (
        f"QUESTION:\n{question}\n\n"
        f"LOG LINES:\n{logs_text}\n\n"
        f"RETRIEVED CASES (filenames & notes):\n{related_text}\n\n"
        "Return ONLY the JSON object."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {
            "answer": "Q&A failed (synthesis error).",
            "confidence": 0.0,
            "citations": [],
        }

    return {
        "answer": data.get("answer", "No answer."),
        "confidence": float(data.get("confidence", 0.6)),
        "citations": _coerce_refs(_safe_list(data.get("citations"), [])),
    }