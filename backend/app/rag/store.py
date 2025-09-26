import os, time, uuid
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from .embedder import embed_texts, embed_one

_INDEX_NAME = os.getenv("PINECONE_INDEX", "agentl3-incidents")
_DIM = 1536
_METRIC = "cosine"
_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
_REGION = os.getenv("PINECONE_REGION", "us-east-1")

def _pc() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY not set")
    return Pinecone(api_key=api_key)

def ensure_index():
    pc = _pc()
    names = [i["name"] for i in pc.list_indexes()]
    if _INDEX_NAME not in names:
        pc.create_index(
            name=_INDEX_NAME,
            dimension=_DIM,
            metric=_METRIC,
            spec=ServerlessSpec(cloud=_CLOUD, region=_REGION),
        )
        while True:
            if pc.describe_index(_INDEX_NAME).status.get("ready"):
                break
            time.sleep(1)

def upsert_texts(texts: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None):
    ensure_index()
    pc = _pc()
    idx = pc.Index(_INDEX_NAME)
    vecs = embed_texts(texts)
    items = []
    for i, emb in enumerate(vecs):
        md = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
        items.append({"id": str(uuid.uuid4()), "values": emb, "metadata": md})
    idx.upsert(items)

def query_similar(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    ensure_index()
    pc = _pc()
    idx = pc.Index(_INDEX_NAME)
    q = embed_one(query_text)
    res = idx.query(vector=q, top_k=top_k, include_metadata=True)
    out = []
    for m in res.matches:
        out.append({"score": float(getattr(m, "score", 0.0)),
                    "metadata": dict(getattr(m, "metadata", {}) or {})})
    return out
