# DocsRAG Lab

Production-style RAG system for technical documentation.

```
NLP/LLM Job Track: [█░░░░░░░░░░░░░░░░░░░] 5/100
```

## Architecture

```
docs source
   ↓
crawler / loader
   ↓
document parser
   ↓
cleaner / normalizer
   ↓
chunker
   ↓
metadata enricher
   ↓
embedding model
   ↓
vector database
   ↓
retriever
   ↓
reranker
   ↓
context builder
   ↓
prompt builder
   ↓
LLM
   ↓
answer + citations
   ↓
evaluation pipeline
```

## Project Structure

```
docsrags-lab/
├── data/
│   ├── raw/
│   ├── processed/
│   └── eval_questions.jsonl
├── src/
│   ├── loaders/
│   ├── preprocessing/
│   ├── chunking/
│   ├── embeddings/
│   ├── vectorstore/
│   ├── retrieval/
│   ├── reranking/
│   ├── generation/
│   ├── evaluation/
│   ├── api/
│   ├── ingest.py
│   ├── chunk.py
│   ├── embed.py
│   ├── retrieve.py
│   ├── rerank.py
│   ├── generate.py
│   └── evaluate.py
├── tests/
├── reports/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Components

| # | Component | Module |
|---|-----------|--------|
| 1 | Ingestion | `src/loaders/` |
| 2 | Preprocessing | `src/preprocessing/` |
| 3 | Chunking | `src/chunking/` |
| 4 | Metadata | `chunk_id`, `source_url`, `title`, `section`, `heading_path` |
| 5 | Embeddings | `src/embeddings/` — bge-small, bge-base, e5-base, OpenAI |
| 6 | Storage | `src/vectorstore/` — Chroma, Qdrant |
| 7 | Retrieval | `src/retrieval/` — vector, BM25, hybrid |
| 8 | Reranking | `src/reranking/` — cross-encoder |
| 9 | Generation | `src/generation/` — context + prompt + LLM |
| 10 | Evaluation | `src/evaluation/` — metrics + report |

## Query Flow

```
user question → query normalization → embedding → top-20 retrieval
→ rerank to top-5 → context assembly → LLM answer → citations validation → response
```

## Eval Flow

```
eval_questions.jsonl → retrieval → check expected_source_url in top-k
→ generation → check expected_keywords → save report to reports/
```

## Quick Start

```bash
cp .env.example .env
pip install -r requirements.txt

# Start API
uvicorn src.api.app:app --reload

# Or with Docker + Qdrant
docker compose up
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + index stats |
| POST | `/ingest` | Run full ingestion pipeline |
| POST | `/query` | Ask a question, get answer + citations |
| POST | `/evaluate` | Run eval pipeline, save report |

## Tech Stack

- Python, FastAPI
- LangChain (loaders)
- Chroma / Qdrant
- SentenceTransformers / OpenAI embeddings
- Custom eval + RAGAS (planned)
- Docker, pytest

## Initial Corpus

LangChain documentation (`docs.langchain.com`).
