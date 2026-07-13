"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    # LLM (Groq)
    groq_api_key: str
    groq_model: str
    groq_base_url: str

    # Embeddings: bge-small | bge-base | e5-base | openai
    openai_api_key: str
    embedding_provider: str
    embedding_model: str

    # Vector store: chroma | qdrant | faiss
    vector_store: str
    chroma_persist_dir: Path
    qdrant_url: str
    qdrant_collection: str

    # Retrieval
    retrieval_top_k: int
    rerank_top_k: int
    use_bm25: bool
    use_hybrid: bool
    reranker_model: str

    # Chunking
    chunk_size: int
    chunk_overlap: int

    # Paths
    raw_data_dir: Path
    processed_data_dir: Path
    eval_questions_path: Path
    reports_dir: Path

    # Logging
    log_level: str

    # Admin endpoints (/ingest, /evaluate)
    admin_api_key: str


def get_config() -> Config:
    return Config(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "bge-small"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "bge-small"),
        vector_store=os.getenv("VECTOR_STORE", "chroma"),
        chroma_persist_dir=PROJECT_ROOT / os.getenv("CHROMA_PERSIST_DIR", "data/processed/chroma"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "docsrag"),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "20")),
        rerank_top_k=int(os.getenv("RERANK_TOP_K", "5")),
        use_bm25=os.getenv("USE_BM25", "false").lower() == "true",
        use_hybrid=os.getenv("USE_HYBRID", "false").lower() == "true",
        reranker_model=os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        raw_data_dir=PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data/raw"),
        processed_data_dir=PROJECT_ROOT / os.getenv("PROCESSED_DATA_DIR", "data/processed"),
        eval_questions_path=PROJECT_ROOT / os.getenv("EVAL_QUESTIONS_PATH", "data/eval_questions.jsonl"),
        reports_dir=PROJECT_ROOT / os.getenv("REPORTS_DIR", "reports"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        admin_api_key=os.getenv("ADMIN_API_KEY", ""),
    )
