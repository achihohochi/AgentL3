from typing import List
from .store import query_similar

def retrieve_related_context(query: str, top_k: int = 3) -> List[str]:
    matches = query_similar(query, top_k=top_k)
    lines = []
    for m in matches:
        md = m.get("metadata", {})
        title = md.get("title") or "related case"
        takeaway = md.get("takeaway") or md.get("summary") or md.get("snippet") or ""
        score = round(m.get("score", 0.0), 3)
        lines.append(f"{title} (score {score}): {takeaway}".strip())
    return lines
