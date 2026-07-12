"""Generate grounded answers with citations."""

from __future__ import annotations

from src.config import Config, get_config
from src.generation.llm import AnswerGenerator
from src.retrieve import retrieve as retrieve_chunks


def generate_answer(
    query: str,
    chunks: list[dict] | None = None,
    config: Config | None = None,
) -> dict:
    """
    Generation pipeline:
    context assembly → LLM answer → citations validation → final response
    """
    config = config or get_config()
    chunks = chunks if chunks is not None else retrieve_chunks(query, config=config)

    generator = AnswerGenerator(config)
    return generator.generate(query, chunks)
