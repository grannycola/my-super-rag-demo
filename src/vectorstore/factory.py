"""Vector store factory."""

from __future__ import annotations

from src.config import Config, get_config
from src.vectorstore.base import VectorStore


def create_vector_store(config: Config | None = None) -> VectorStore:
    config = config or get_config()
    store_type = config.vector_store.lower()

    if store_type == "chroma":
        from src.vectorstore.chroma_store import ChromaVectorStore

        return ChromaVectorStore(config)
    if store_type == "qdrant":
        from src.vectorstore.qdrant_store import QdrantVectorStore

        return QdrantVectorStore(config)

    raise ValueError(f"Unknown vector store: {store_type}. Supported: chroma, qdrant")
