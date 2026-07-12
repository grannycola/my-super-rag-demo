"""Retrieve relevant chunks: query normalization → embedding → top-k retrieval."""

from __future__ import annotations

from src.config import Config, get_config
from src.retrieval.hybrid import HybridRetriever
from src.reranking.cross_encoder import get_reranker


def retrieve(
    query: str,
    top_k: int | None = None,
    rerank: bool = True,
    config: Config | None = None,
) -> list[dict]:
    """
    Query flow (retrieval stage):
    user question → query normalization → embedding → top-20 retrieval → rerank to top-5
    """
    config = config or get_config()
    retriever = HybridRetriever(config)
    chunks = retriever.retrieve(query, top_k=top_k or config.retrieval_top_k)

    if rerank and chunks:
        reranker = get_reranker(config)
        chunks = reranker.rerank(query, chunks, top_k=config.rerank_top_k)

    return chunks
