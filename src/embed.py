"""Embed chunks and persist to vector database."""

from __future__ import annotations

import json

from src.chunking.models import DocumentChunk
from src.config import Config, get_config
from src.embeddings.factory import create_embedding_model
from src.vectorstore.factory import create_vector_store


def embed_and_store(chunks: list[dict] | None = None, config: Config | None = None) -> int:
    """
    Pipeline stage: embedding model → vector database.
    Returns number of chunks indexed.
    """
    config = config or get_config()

    if chunks is None:
        chunks_path = config.processed_data_dir / "chunks" / "chunks.jsonl"
        chunks = []
        for line in chunks_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(json.loads(line))

    if not chunks:
        return 0

    doc_chunks = [
        DocumentChunk(
            chunk_id=c["chunk_id"],
            text=c["text"],
            source_url=c["source_url"],
            title=c["title"],
            section=c.get("section", ""),
            heading_path=c.get("heading_path", []),
            doc_type=c.get("doc_type", "markdown"),
            last_updated=c.get("last_updated"),
        )
        for c in chunks
    ]

    embedding_model = create_embedding_model(config)
    texts = [chunk.text for chunk in doc_chunks]
    embeddings = embedding_model.embed_documents(texts)

    vector_store = create_vector_store(config)
    vector_store.add_chunks(doc_chunks, embeddings)

    return len(doc_chunks)
