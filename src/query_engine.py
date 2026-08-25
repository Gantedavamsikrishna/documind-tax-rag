"""Retrieve Income-tax Act sections from ChromaDB and answer with Groq."""

from __future__ import annotations

import os
from pathlib import Path
import re

import chromadb
from dotenv import load_dotenv
from groq import Groq, GroqError
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "income_tax_act"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
GROQ_MODEL = "openai/gpt-oss-20b"

_embedder: SentenceTransformer | None = None
_collection: chromadb.Collection | None = None
_groq_client: Groq | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_collection(name=COLLECTION_NAME)
    return _collection


def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set in .env.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def answer_query(question: str, k: int = 2) -> tuple[str, list[str]]:
    """Answer a question using only the top-k retrieved statutory sections."""
    if not question.strip():
        raise ValueError("Question must not be empty.")
    if k < 1:
        raise ValueError("k must be at least 1.")

    section_match = re.search(
        r"\bsection\s+(\d+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)",
        question,
        re.IGNORECASE,
    )
    if section_match:
        section_id = section_match.group(1).upper()
        direct = get_collection().get(
            ids=[section_id], include=["documents", "metadatas"]
        )
        documents = direct["documents"]
        metadatas = direct["metadatas"]

        if not documents:
            base_id = re.sub(r"\([0-9A-Za-z]+\)$", "", section_id)
            if base_id != section_id:
                direct = get_collection().get(
                    ids=[base_id], include=["documents", "metadatas"]
                )
                documents = direct["documents"]
                metadatas = direct["metadatas"]

    else:
        documents = []
        metadatas = []

    if not documents:
        question_embedding = get_embedder().encode(
            question, normalize_embeddings=True
        ).tolist()
        results = get_collection().query(
            query_embeddings=[question_embedding],
            n_results=k,
            include=["documents", "metadatas"],
        )
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

    sections = [metadata["section"] for metadata in metadatas]
    MAX_CHARS_PER_CHUNK = 2000  # roughly ~500 tokens per chunk

    def truncate(text: str, limit: int = MAX_CHARS_PER_CHUNK) -> str:
        return text if len(text) <= limit else text[:limit] + "\n...[truncated]"

    context = "\n\n".join(
        f"Section {metadata['section']} ({metadata.get('chapter', 'Unknown chapter')}):\n{truncate(document)}"
        for document, metadata in zip(documents, metadatas)
    )

    prompt = f"""You answer questions about the Indian Income-tax Act, 1961.
Use only the retrieved statutory context below. Do not use outside knowledge.
If the context does not support an answer, say that the retrieved context is insufficient.
Cite the applicable section number(s) in your answer.

Retrieved context:
{context}

Question: {question}
"""
    completion = get_groq_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return completion.choices[0].message.content or "", sections


def main() -> None:
    print("DocuMind Income-tax Act Q&A. Type 'exit' to quit.")
    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if question.lower() == "exit":
            break
        try:
            answer, sections = answer_query(question)
        except (GroqError, RuntimeError, ValueError) as error:
            print(f"Error: {error}")
            continue

        print(f"\nAnswer:\n{answer}")
        print(f"\nRetrieved sections: {', '.join(sections)}")


if __name__ == "__main__":
    main()
