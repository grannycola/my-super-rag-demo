"""Base embedding model interface."""

from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...
