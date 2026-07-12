"""Vector similarity retrieval."""

from __future__ import annotations

from src.config import Config, get_config
from src.embeddings.factory import create_embedding_model
from src.vectorstore.factory import create_vector_store


class VectorRetriever:
    """Retrieve chunks via vector similarity search."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()
        self.embedding_model = create_embedding_model(self.config)
        self.vector_store = create_vector_store(self.config)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[dict]:
        top_k = top_k or self.config.retrieval_top_k
        normalized_query = self._normalize_query(query)
        query_embedding = self.embedding_model.embed_query(normalized_query)
        return self.vector_store.search(query_embedding, top_k=top_k, filters=filters)

    @staticmethod
    def _normalize_query(query: str) -> str:
        return " ".join(query.strip().split())
