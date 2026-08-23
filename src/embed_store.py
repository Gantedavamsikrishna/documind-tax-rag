"""Embed Income-tax Act sections and persist them in ChromaDB."""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks" / "sections.json"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "income_tax_act"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
BATCH_SIZE = 64


def chroma_ids(chunks: list[dict[str, str]]) -> list[str]:
    """Return stable, unique IDs while preserving section identifiers in metadata."""
    totals = Counter(chunk["section"] for chunk in chunks)
    seen: Counter[str] = Counter()
    ids: list[str] = []
    for chunk in chunks:
        section = chunk["section"]
        seen[section] += 1
        ids.append(section if totals[section] == 1 else f"{section}__{seen[section]}")
    return ids


def main() -> None:
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    ids = chroma_ids(chunks)
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        batch_ids = ids[start : start + BATCH_SIZE]
        texts = [chunk["text"] for chunk in batch]
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()
        collection.upsert(
            ids=batch_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                {"section": chunk["section"], "chapter": chunk["chapter"]}
                for chunk in batch
            ],
        )

    print(f"Chunks embedded and stored: {len(chunks)}")


if __name__ == "__main__":
    main()
