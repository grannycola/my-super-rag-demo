"""LLM answer generation with citations validation."""

from __future__ import annotations

import re

from src.config import Config, get_config
from src.generation.context_builder import ContextBuilder
from src.generation.prompt_builder import PromptBuilder

CITATION_PATTERN = re.compile(r"\[(\d+)\]")
REFUSAL_PHRASE = "don't have enough information"


class AnswerGenerator:
    """Generate grounded answers and validate citations."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()

    def generate(self, query: str, chunks: list[dict]) -> dict:
        context, cited_chunks = self.context_builder.build(chunks)

        if not context.strip():
            return {
                "answer": "I don't have enough information in the documentation to answer this question.",
                "citations": [],
                "refused": True,
            }

        messages = self.prompt_builder.build(query, context)
        answer = self._call_llm(messages)
        citations = self._extract_citations(answer, cited_chunks)
        refused = REFUSAL_PHRASE in answer.lower()

        return {
            "answer": answer,
            "citations": citations,
            "refused": refused,
            "context_chunks": cited_chunks,
        }

    def _call_llm(self, messages: list[dict]) -> str:
        if not self.config.groq_api_key:
            return (
                "LLM is not configured (missing GROQ_API_KEY). "
                "Retrieved context is available but answer generation is skipped."
            )

        from openai import OpenAI

        client = OpenAI(
            api_key=self.config.groq_api_key,
            base_url=self.config.groq_base_url,
        )
        response = client.chat.completions.create(
            model=self.config.groq_model,
            messages=messages,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    @staticmethod
    def _extract_citations(answer: str, chunks: list[dict]) -> list[dict]:
        cited_indices = {int(m.group(1)) for m in CITATION_PATTERN.finditer(answer)}
        citations: list[dict] = []
        for i, chunk in enumerate(chunks, start=1):
            if i in cited_indices:
                citations.append(
                    {
                        "citation_id": f"[{i}]",
                        "source_url": chunk.get("source_url", ""),
                        "title": chunk.get("title", ""),
                        "section": chunk.get("section", ""),
                        "chunk_id": chunk.get("chunk_id", ""),
                    }
                )
        return citations
