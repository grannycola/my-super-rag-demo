"""Hybrid retrieval: vector + BM25 (optional)."""

from __future__ import annotations

from src.config import Config, get_config
from src.retrieval.vector import VectorRetriever


class HybridRetriever:
    """Combine vector and keyword search results."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()
        self.vector_retriever = VectorRetriever(self.config)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[dict]:
        top_k = top_k or self.config.retrieval_top_k
        vector_results = self.vector_retriever.retrieve(query, top_k=top_k, filters=filters)

        if not self.config.use_hybrid and not self.config.use_bm25:
            return vector_results

        # TODO: implement BM25 and reciprocal rank fusion
        return vector_results
