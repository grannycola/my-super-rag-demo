"""Base vector store interface."""

from abc import ABC, abstractmethod

from src.chunking.models import DocumentChunk


class VectorStore(ABC):
    @abstractmethod
    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def count(self) -> int:
        ...
