"""Rerank retrieved chunks to top-k."""

from __future__ import annotations

from src.config import Config, get_config
from src.reranking.cross_encoder import CrossEncoderReranker


def rerank(
    query: str,
    chunks: list[dict],
    top_k: int | None = None,
    config: Config | None = None,
) -> list[dict]:
    """Rerank chunks using cross-encoder. Returns top-k compressed results."""
    config = config or get_config()
    reranker = CrossEncoderReranker(config)
    return reranker.rerank(query, chunks, top_k=top_k or config.rerank_top_k)
