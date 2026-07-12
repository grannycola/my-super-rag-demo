"""Run evaluation over eval_questions.jsonl and save report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import Config, get_config
from src.evaluation.metrics import check_keywords, check_source_in_top_k, recall_at_k
from src.generate import generate_answer
from src.retrieve import retrieve


class EvaluationRunner:
    """Evaluate retrieval and generation quality."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()

    def load_questions(self, path: Path | None = None) -> list[dict]:
        path = path or self.config.eval_questions_path
        questions: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                questions.append(json.loads(line))
        return questions

    def run(self, questions_path: Path | None = None) -> dict:
        questions = self.load_questions(questions_path)
        results: list[dict] = []

        for item in questions:
            question = item["question"]
            expected_url = item.get("expected_source_url", "")
            expected_keywords = item.get("expected_keywords", [])

            chunks = retrieve(question)
            retrieval_hit = check_source_in_top_k(
                chunks, expected_url, self.config.retrieval_top_k
            ) if expected_url else None

            answer_result = generate_answer(question, chunks)
            keyword_check = check_keywords(answer_result["answer"], expected_keywords)

            results.append(
                {
                    "id": item.get("id"),
                    "question": question,
                    "expected_source_url": expected_url,
                    "expected_keywords": expected_keywords,
                    "retrieval_hit": retrieval_hit,
                    "recall_at_5": recall_at_k(chunks, expected_url, 5) if expected_url else None,
                    "recall_at_20": recall_at_k(chunks, expected_url, 20) if expected_url else None,
                    "keyword_check": keyword_check,
                    "answer": answer_result["answer"],
                    "citations": answer_result.get("citations", []),
                }
            )

        report = self._aggregate(results)
        self._save_report(report)
        return report

    def _aggregate(self, results: list[dict]) -> dict:
        retrieval_results = [r["retrieval_hit"] for r in results if r["retrieval_hit"] is not None]
        keyword_results = [r["keyword_check"]["passed"] for r in results if r.get("expected_keywords")]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_questions": len(results),
            "retrieval_recall": sum(retrieval_results) / len(retrieval_results) if retrieval_results else None,
            "keyword_pass_rate": sum(keyword_results) / len(keyword_results) if keyword_results else None,
            "results": results,
        }

    def _save_report(self, report: dict) -> Path:
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.config.reports_dir / f"eval_{timestamp}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
