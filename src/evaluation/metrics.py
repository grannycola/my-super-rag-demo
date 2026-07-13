"""Evaluation metrics."""

from __future__ import annotations

from src.loaders.url_manifest import resolve_source_url


def normalize_doc_url(url: str) -> str:
    """Normalize documentation URLs for comparison."""
    normalized = url.strip().rstrip("/")
    if normalized.endswith(".md"):
        normalized = normalized[:-3]
    return normalized.lower()


def resolve_chunk_source_url(chunk: dict) -> str:
    source_url = chunk.get("source_url", "")
    if source_url.startswith("file://"):
        return resolve_source_url(source_url)
    return source_url


def check_source_in_top_k(chunks: list[dict], expected_source_url: str, top_k: int) -> bool:
    expected = normalize_doc_url(expected_source_url)
    for chunk in chunks[:top_k]:
        resolved = resolve_chunk_source_url(chunk)
        if normalize_doc_url(resolved) == expected:
            return True
    return False


def check_keywords(answer: str, expected_keywords: list[str]) -> dict:
    answer_lower = answer.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    return {
        "matched": matched,
        "missing": [kw for kw in expected_keywords if kw.lower() not in answer_lower],
        "passed": len(matched) == len(expected_keywords) if expected_keywords else True,
    }


def recall_at_k(chunks: list[dict], expected_source_url: str, k: int) -> float:
    return 1.0 if check_source_in_top_k(chunks, expected_source_url, k) else 0.0
