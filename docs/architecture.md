# Architecture

## Pipeline Overview

```
docs source
   ↓
crawler / loader          → src/loaders/
   ↓
document parser
   ↓
cleaner / normalizer      → src/preprocessing/
   ↓
chunker                   → src/chunking/
   ↓
metadata enricher
   ↓
embedding model           → src/embeddings/
   ↓
vector database           → src/vectorstore/
   ↓
retriever                 → src/retrieval/
   ↓
reranker                  → src/reranking/
   ↓
context builder           → src/generation/
   ↓
prompt builder
   ↓
LLM
   ↓
answer + citations
   ↓
evaluation pipeline       → src/evaluation/
```

## Orchestration Modules

Top-level pipeline entry points in `src/`:

| Module | Stage |
|--------|-------|
| `ingest.py` | loader → cleaner → normalizer → chunker |
| `chunk.py` | chunk raw documents |
| `embed.py` | embed chunks → vector store |
| `retrieve.py` | normalize → embed → retrieve → rerank |
| `rerank.py` | cross-encoder top-k compression |
| `generate.py` | context → LLM → citations |
| `evaluate.py` | eval questions → metrics → report |

## API

FastAPI app in `src/api/`:

```
FastAPI app
   ├── /ingest
   ├── /query
   ├── /evaluate
   └── /health
```

## Metadata Schema

Each chunk carries:

- `source_url`
- `title`
- `section`
- `heading_path`
- `doc_type`
- `chunk_id`
- `last_updated`

## Configuration

All settings via environment variables in `src/config.py`. See `.env.example`.

## Data Directories

- `data/raw/` — fetched documentation
- `data/processed/` — chunks + vector index
- `data/eval_questions.jsonl` — evaluation dataset
- `reports/` — evaluation reports

## Planned Extensions

- Airflow ingestion DAG
- Change detection for updated docs
- RAGAS integration
- BM25 + hybrid search (RRF)
- Streamlit demo UI
