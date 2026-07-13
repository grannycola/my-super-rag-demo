"""Tests for evaluation metrics."""

from src.evaluation.metrics import (
    check_keywords,
    check_source_in_top_k,
    normalize_doc_url,
    recall_at_k,
)


def test_check_source_in_top_k():
    chunks = [
        {"source_url": "https://a.com"},
        {"source_url": "https://b.com"},
        {"source_url": "https://c.com"},
    ]
    assert check_source_in_top_k(chunks, "https://c.com", top_k=2) is False
    assert check_source_in_top_k(chunks, "https://b.com", top_k=2) is True


def test_check_source_in_top_k_normalizes_md_suffix():
    chunks = [{"source_url": "https://docs.langchain.com/langsmith/evaluate-rag-tutorial.md"}]
    expected = "https://docs.langchain.com/langsmith/evaluate-rag-tutorial"
    assert check_source_in_top_k(chunks, expected, top_k=1) is True


def test_normalize_doc_url():
    assert normalize_doc_url("https://Example.com/page.md/") == "https://example.com/page"


def test_check_keywords():
    result = check_keywords("Use a retriever for retrieval tasks", ["retriever", "missing"])
    assert "retriever" in result["matched"]
    assert "missing" in result["missing"]
    assert result["passed"] is False


def test_recall_at_k():
    chunks = [{"source_url": "https://expected.com"}]
    assert recall_at_k(chunks, "https://expected.com", k=5) == 1.0
    assert recall_at_k(chunks, "https://other.com", k=5) == 0.0
