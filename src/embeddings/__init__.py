"""Embedding models: bge-small, bge-base, e5-base, OpenAI."""

from src.embeddings.base import EmbeddingModel
from src.embeddings.factory import create_embedding_model

__all__ = ["EmbeddingModel", "create_embedding_model"]
