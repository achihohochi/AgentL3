from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


import os, glob
from app.rag.store import upsert_texts

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KNOW = os.path.abspath(os.path.join(ROOT, "data", "knowledge"))

def _read_cases():
    texts, metas = [], []
    for p in glob.glob(os.path.join(KNOW, "*.md")):
        with open(p, "r") as f:
            raw = f.read().strip()
        title = ""; takeaway = ""
        for line in raw.splitlines():
            low = line.lower()
            if low.startswith("title:"): title = line.split(":",1)[1].strip()
            if low.startswith("takeaway:"): takeaway = line.split(":",1)[1].strip()
        texts.append(raw)
        metas.append({"title": title or os.path.basename(p), "takeaway": takeaway, "path": p})
    return texts, metas

if __name__ == "__main__":
    texts, metas = _read_cases()
    if not texts:
        raise SystemExit("No knowledge files found to seed.")
    upsert_texts(texts, metas)
    print(f"Seeded {len(texts)} cases.")
