"""Qdrant vector store implementation."""

from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.chunking.models import DocumentChunk
from src.config import Config
from src.vectorstore.base import VectorStore


class QdrantVectorStore(VectorStore):
    UPSERT_BATCH_SIZE = 500

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = QdrantClient(url=config.qdrant_url)
        self.collection_name = config.qdrant_collection
        self._dimension: int | None = None

    def _ensure_collection(self, dimension: int) -> None:
        if self._dimension == dimension:
            return
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
        self._dimension = dimension

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return

        self._ensure_collection(len(embeddings[0]))
        points = [
            PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "source_url": chunk.source_url,
                    "title": chunk.title,
                    "section": chunk.section,
                    "heading_path": " > ".join(chunk.heading_path),
                    "doc_type": chunk.doc_type,
                    "last_updated": chunk.last_updated or "",
                },
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        for start in range(0, len(chunks), self.UPSERT_BATCH_SIZE):
            end = start + self.UPSERT_BATCH_SIZE
            batch_points = points[start:end]
            self.client.upsert(collection_name=self.collection_name, points=batch_points)

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=None,  # TODO: metadata filters
        )

        return [
            {
                "chunk_id": hit.payload.get("chunk_id", ""),
                "text": hit.payload.get("text", ""),
                "source_url": hit.payload.get("source_url", ""),
                "title": hit.payload.get("title", ""),
                "section": hit.payload.get("section", ""),
                "heading_path": hit.payload.get("heading_path", ""),
                "doc_type": hit.payload.get("doc_type", ""),
                "score": hit.score,
                "metadata": hit.payload,
            }
            for hit in results
        ]

    def count(self) -> int:
        info = self.client.get_collection(self.collection_name)
        return info.points_count or 0
