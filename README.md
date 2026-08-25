# DocuMind — Income Tax Act RAG Q&A System

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6B6B?style=flat)
![Groq](https://img.shields.io/badge/Groq-LLM%20Inference-F55036?style=flat)
![sentence-transformers](https://img.shields.io/badge/sentence--transformers-Embeddings-4B8BBE?style=flat)
![License](https://img.shields.io/badge/License-Educational-lightgrey?style=flat)

A domain-specific Retrieval-Augmented Generation (RAG) system that answers questions about the Indian Income-tax Act, 1961, with statutory section citations. Built entirely on free-tier tools, running locally.

> **Ask a question about Indian tax law, get an answer grounded in the actual statute — with the exact section cited.**

---

## Why this project

Generic "chat with your PDF" RAG demos are common. This project is different in three ways:

1. **Domain-specific and genuinely useful** — not a toy dataset, but the full ~300-section Income-tax Act, 1961, sourced directly from the government's own document.
2. **Citation-first design** — every answer is required to cite the specific section it came from, and the system is instructed to say "insufficient context" rather than guess when the retrieved text doesn't cover the question.
3. **Measured, not assumed** — includes an evaluation harness with real accuracy numbers (see [Evaluation Results](#evaluation-results)), not just "it seems to work."

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| 🧠 **Embeddings** | `BAAI/bge-small-en-v1.5` (sentence-transformers) | Converts text into vectors — runs locally, no API key |
| 🗄️ **Vector Store** | ChromaDB | Local, persistent vector database |
| ⚡ **LLM Inference** | Groq (`openai/gpt-oss-20b`) | Free-tier, low-latency generation |
| 🐍 **Language** | Python 3.12 | Core pipeline and CLI |
| 🔑 **Config** | python-dotenv | API key management |

---

## System Architecture

### Pipeline

```
Raw Act (.txt)
      │
      ▼
clean_text.py         → strips PDF export noise (page headers, timestamps, footers)
      │
      ▼
chunk_and_embed.py     → splits into one chunk per statutory section
      │
      ▼
split_definitions.py   → splits Section 2 (Definitions) into one chunk
      │                    per individual defined term
      ▼
embed_store.py          → embeds each chunk and stores it in ChromaDB
      │
      ▼
query_engine.py          → retrieval (exact-match section lookup, falling
                            back to vector similarity) + generation (Groq)
```

### Retrieval + generation flow

```
┌──────────────────┐    ┌───────────────────┐    ┌────────────────────┐
│   Tax Act Text    │───▶│  Chunking Module   │───▶│      ChromaDB       │
└──────────────────┘    └───────────────────┘    │  (Vector Store)     │
                                                      └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      ┌──────────────────────┐
                                                      │     Query Engine      │
                                                      │  • Exact-match lookup  │
                                                      │    (section number)    │
                                                      │  • Vector similarity   │
                                                      │    search (fallback)   │
                                                      └──────────┬───────────┘
                                                                 │
                                                                 ▼
                                                      ┌──────────────────────┐
                                                      │   Groq LLM (generate)  │
                                                      │  grounded answer with   │
                                                      │  section citation       │
                                                      └──────────────────────┘
```

---

## Evaluation Results

Measured against a 17-question test set covering specific-section lookups, conceptual/definitional questions, and two adversarial "trick" questions designed to test hallucination resistance (questions the Act cannot answer, e.g. GST rates, or superseded historical tax rates).

| Metric | Score | What it measures |
|---|---|---|
| 🎯 **Retrieval accuracy** | **100%** | Did the correct statutory section get pulled from the vector database? |
| 📝 **Citation accuracy** | **93.3%** | Did the LLM's written answer correctly cite the retrieved section? |
| 🛡️ **Hallucination resistance** | **100%** | On questions outside the Act's scope, did the system correctly decline instead of inventing an answer? |

Full per-question results: [`data/eval/results.json`](data/eval/results.json)
Test set: [`data/eval/test_questions.json`](data/eval/test_questions.json)
Harness: [`src/evaluate.py`](src/evaluate.py)

---

## Setup

```bash
# 1. Clone and set up environment
git clone <your-repo-url>
cd documind-tax-rag
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Place the source Act text
# Download from incometaxindia.gov.in and place at:
# data/raw/income_tax_act_1961.txt

# 4. Build the pipeline (run once)
python src/clean_text.py
python src/chunk_and_embed.py
python src/split_definitions.py
python src/embed_store.py

# 5. Run the Q&A CLI
python src/query_engine.py
```

## Running the evaluation

```bash
python src/evaluate.py
```

---

## Example queries

```
> What is the definition of a 'Capital Asset'?
> What is section 80C?
> What are the tax slabs under the new concessional tax regime of Section 115BAC?
> Explain the tax exemptions available on the sale of a residential house under Section 54.
```

---

## Project structure

```
documind-tax-rag/
├── data/
│   ├── raw/                # source Act text
│   ├── cleaned/             # noise-stripped text
│   ├── chunks/              # section-level JSON chunks
│   └── eval/                 # test questions + evaluation results
├── src/
│   ├── clean_text.py
│   ├── chunk_and_embed.py
│   ├── split_definitions.py
│   ├── embed_store.py
│   ├── query_engine.py
│   └── evaluate.py
├── chroma_db/                # persistent vector store (gitignored)
├── .env                       # API key (gitignored)
└── README.md
```

---

## License

Educational/portfolio project. The Income-tax Act, 1961 text is a public government document.
