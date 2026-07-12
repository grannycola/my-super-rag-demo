"""Assemble context from reranked chunks."""

from __future__ import annotations


class ContextBuilder:
    """Build LLM context from retrieved chunks with token budget."""

    def __init__(self, max_chars: int = 12000) -> None:
        self.max_chars = max_chars

    def build(self, chunks: list[dict]) -> tuple[str, list[dict]]:
        parts: list[str] = []
        used_chunks: list[dict] = []
        total_chars = 0

        for i, chunk in enumerate(chunks, start=1):
            citation_id = f"[{i}]"
            block = (
                f"{citation_id} {chunk.get('title', 'Unknown')} — "
                f"{chunk.get('source_url', '')}\n"
                f"Section: {chunk.get('section', '')}\n"
                f"{chunk.get('text', '')}\n"
            )
            if total_chars + len(block) > self.max_chars:
                break
            parts.append(block)
            used_chunks.append({**chunk, "citation_id": citation_id})
            total_chars += len(block)

        return "\n---\n".join(parts), used_chunks
