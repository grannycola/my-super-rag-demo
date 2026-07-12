"""Evaluation metrics."""

from __future__ import annotations


def check_source_in_top_k(chunks: list[dict], expected_source_url: str, top_k: int) -> bool:
    urls = [chunk.get("source_url", "") for chunk in chunks[:top_k]]
    return expected_source_url in urls


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
