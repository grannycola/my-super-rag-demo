"""Chroma vector store implementation."""

from __future__ import annotations

import chromadb

from src.chunking.models import DocumentChunk
from src.config import Config
from src.vectorstore.base import VectorStore


class ChromaVectorStore(VectorStore):
    COLLECTION_NAME = "docsrag"
    UPSERT_BATCH_SIZE = 500

    def __init__(self, config: Config) -> None:
        self.config = config
        config.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(config.chroma_persist_dir))
        self.collection = self.client.get_or_create_collection(name=self.COLLECTION_NAME)

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source_url": chunk.source_url,
                "title": chunk.title,
                "section": chunk.section,
                "heading_path": " > ".join(chunk.heading_path),
                "doc_type": chunk.doc_type,
                "chunk_id": chunk.chunk_id,
                "last_updated": chunk.last_updated or "",
            }
            for chunk in chunks
        ]

        for start in range(0, len(chunks), self.UPSERT_BATCH_SIZE):
            end = start + self.UPSERT_BATCH_SIZE
            self.collection.upsert(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        where = filters or None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return chunks

        for i, chunk_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else None
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "source_url": metadata.get("source_url", ""),
                    "title": metadata.get("title", ""),
                    "section": metadata.get("section", ""),
                    "heading_path": metadata.get("heading_path", ""),
                    "doc_type": metadata.get("doc_type", ""),
                    "score": 1.0 - (distance or 0.0),
                    "metadata": metadata,
                }
            )

        return chunks

    def count(self) -> int:
        return self.collection.count()
