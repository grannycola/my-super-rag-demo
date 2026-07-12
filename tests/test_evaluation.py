"""Tests for evaluation metrics."""

from src.evaluation.metrics import check_keywords, check_source_in_top_k, recall_at_k


def test_check_source_in_top_k():
    chunks = [
        {"source_url": "https://a.com"},
        {"source_url": "https://b.com"},
        {"source_url": "https://c.com"},
    ]
    assert check_source_in_top_k(chunks, "https://c.com", top_k=2) is False
    assert check_source_in_top_k(chunks, "https://b.com", top_k=2) is True


def test_check_keywords():
    result = check_keywords("Use a retriever for retrieval tasks", ["retriever", "missing"])
    assert "retriever" in result["matched"]
    assert "missing" in result["missing"]
    assert result["passed"] is False


def test_recall_at_k():
    chunks = [{"source_url": "https://expected.com"}]
    assert recall_at_k(chunks, "https://expected.com", k=5) == 1.0
    assert recall_at_k(chunks, "https://other.com", k=5) == 0.0
