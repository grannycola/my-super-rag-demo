"""Build prompts for grounded answer generation."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a technical documentation assistant.
Answer the user's question using ONLY the provided context.
If the context is insufficient, say you don't have enough information.
Always cite sources using [1], [2], etc. matching the context blocks — sparingly, usually once at the end of a paragraph, not after every phrase.
Format answers in Markdown. Use fenced code blocks with language tags (```python, ```typescript) for code examples."""

REFUSAL_HINT = "If context is insufficient, respond with: I don't have enough information in the documentation to answer this question."


class PromptBuilder:
    """Build system and user prompts for the LLM."""

    def build(self, query: str, context: str) -> list[dict]:
        user_content = f"""Context:
{context}

Question: {query}

Provide a clear answer with citations. {REFUSAL_HINT}"""

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
