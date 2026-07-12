"""Cross-encoder reranker for top-k compression."""

from __future__ import annotations

from src.config import Config, get_config


class CrossEncoderReranker:
    """Rerank retrieved chunks using a cross-encoder model."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.config.reranker_model)
        return self._model

    def rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int | None = None,
    ) -> list[dict]:
        top_k = top_k or self.config.rerank_top_k
        if not chunks:
            return []

        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        results: list[dict] = []
        for chunk, score in ranked[:top_k]:
            chunk = {**chunk, "rerank_score": float(score)}
            results.append(chunk)

        return results
