"""Tests for retrieval evaluation script."""

import json
from pathlib import Path
from unittest.mock import patch

from src.evaluate_retrieval import (
    REPORT_FILENAME,
    evaluate_retrieval,
    load_questions,
    save_report,
)


def test_load_questions(tmp_path: Path):
    path = tmp_path / "questions.jsonl"
    path.write_text(
        '{"id": "q1", "question": "test?", "expected_source_url": "https://a.com"}\n',
        encoding="utf-8",
    )
    questions = load_questions(path)
    assert len(questions) == 1
    assert questions[0]["id"] == "q1"


def test_evaluate_retrieval_with_mock(tmp_path: Path):
    path = tmp_path / "questions.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "q1",
                "question": "What is RAG?",
                "expected_source_url": "https://expected.com",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    mock_chunks = [
        {"source_url": "https://other.com", "text": "other"},
        {"source_url": "https://expected.com", "text": "target"},
    ]

    with patch("src.evaluate_retrieval.retrieve", return_value=mock_chunks):
        report = evaluate_retrieval(questions_path=path, top_k=5)

    assert report["total"] == 1
    assert report["top_k"] == 5
    assert report["hits"] == 1
    assert report["hit_rate"] == 1.0
    assert report["results"][0]["found"] is True
    assert report["results"][0]["retrieved_urls"] == [
        "https://other.com",
        "https://expected.com",
    ]


def test_save_report(tmp_path: Path):
    import os

    from src.config import get_config

    os.environ["REPORTS_DIR"] = str(tmp_path / "reports")
    config = get_config()
    report = {"total": 0, "hits": 0, "hit_rate": 0.0, "results": []}
    path = save_report(report, config)
    assert path.exists()
    assert path.name == REPORT_FILENAME
