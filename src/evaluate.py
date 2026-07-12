"""Run evaluation pipeline over eval_questions.jsonl."""

from __future__ import annotations

from pathlib import Path

from src.config import Config, get_config
from src.evaluation.runner import EvaluationRunner


def evaluate(questions_path: Path | None = None, config: Config | None = None) -> dict:
    """
    Eval flow:
    eval_questions.jsonl → retrieval → check expected_source_url →
    generation → check expected_keywords → save report
    """
    config = config or get_config()
    runner = EvaluationRunner(config)
    return runner.run(questions_path)
