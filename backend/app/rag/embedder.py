from typing import List
from openai import OpenAI
import os

_EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts: return []
    resp = _client.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

def embed_one(text: str) -> List[float]:
    return embed_texts([text])[0]
