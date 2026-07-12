"""Embedding model factory."""

from __future__ import annotations

from src.config import Config, get_config
from src.embeddings.base import EmbeddingModel


class OpenAIEmbeddingModel(EmbeddingModel):
    def __init__(self, model: str, api_key: str) -> None:
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(api_key=api_key)
        self._dimension = 1536

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    @property
    def dimension(self) -> int:
        return self._dimension


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    MODEL_MAP = {
        "bge-small": "BAAI/bge-small-en-v1.5",
        "bge-base": "BAAI/bge-base-en-v1.5",
        "e5-base": "intfloat/e5-base-v2",
    }

    def __init__(self, model_key: str) -> None:
        from sentence_transformers import SentenceTransformer

        model_name = self.MODEL_MAP.get(model_key, model_key)
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    @property
    def dimension(self) -> int:
        return self._dimension


def create_embedding_model(config: Config | None = None) -> EmbeddingModel:
    config = config or get_config()
    provider = config.embedding_provider.lower()

    if provider == "openai":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
        return OpenAIEmbeddingModel(config.embedding_model, config.openai_api_key)

    if provider in SentenceTransformerEmbeddingModel.MODEL_MAP or provider == "sentence-transformers":
        model_key = config.embedding_model if provider == "sentence-transformers" else provider
        return SentenceTransformerEmbeddingModel(model_key)

    raise ValueError(f"Unknown embedding provider: {provider}")
