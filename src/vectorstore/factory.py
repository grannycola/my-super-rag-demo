"""Vector store factory."""

from __future__ import annotations

from src.config import Config, get_config
from src.vectorstore.base import VectorStore

_vector_store: VectorStore | None = None


def create_vector_store(config: Config | None = None) -> VectorStore:
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    config = config or get_config()
    store_type = config.vector_store.lower()

    if store_type == "chroma":
        from src.vectorstore.chroma_store import ChromaVectorStore

        _vector_store = ChromaVectorStore(config)
        return _vector_store
    if store_type == "qdrant":
        from src.vectorstore.qdrant_store import QdrantVectorStore

        _vector_store = QdrantVectorStore(config)
        return _vector_store

    raise ValueError(f"Unknown vector store: {store_type}. Supported: chroma, qdrant")
