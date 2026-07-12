"""Evaluate retrieval: question → retrieve top_k → check expected_source_url → report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import Config, get_config
from src.evaluation.metrics import check_source_in_top_k
from src.retrieve import retrieve

REPORT_FILENAME = "retrieval_eval.json"


def load_questions(path: Path) -> list[dict]:
    questions: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            questions.append(json.loads(line))
    return questions


def evaluate_retrieval(
    questions_path: Path | None = None,
    top_k: int | None = None,
    config: Config | None = None,
) -> dict:
    config = config or get_config()
    top_k = top_k or config.retrieval_top_k
    path = questions_path or config.eval_questions_path
    questions = load_questions(path)

    results: list[dict] = []
    hits = 0

    for item in questions:
        question = item["question"]
        expected_url = item.get("expected_source_url", "")

        chunks = retrieve(question, top_k=top_k, rerank=False, config=config)
        retrieved_urls = [c.get("source_url", "") for c in chunks[:top_k]]
        found = check_source_in_top_k(chunks, expected_url, top_k) if expected_url else False

        if found:
            hits += 1

        results.append(
            {
                "id": item.get("id"),
                "question": question,
                "expected_source_url": expected_url,
                "found": found,
                "retrieved_urls": retrieved_urls,
            }
        )

    total = len(results)
    return {
        "total": total,
        "top_k": top_k,
        "hits": hits,
        "hit_rate": hits / total if total else 0.0,
        "results": results,
    }


def save_report(report: dict, config: Config | None = None) -> Path:
    config = config or get_config()
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    path = config.reports_dir / REPORT_FILENAME
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality")
    parser.add_argument(
        "--questions",
        type=Path,
        default=None,
        help="Path to eval_questions.jsonl",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Number of chunks to retrieve (default: RETRIEVAL_TOP_K from config)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print report to stdout without saving",
    )
    args = parser.parse_args()

    report = evaluate_retrieval(questions_path=args.questions, top_k=args.top_k)

    if args.no_save:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        path = save_report(report)
        print(f"Retrieval eval: {report['hits']}/{report['total']} hits "
              f"(hit@{report['top_k']} = {report['hit_rate']:.2%})")
        print(f"Report saved to: {path}")


if __name__ == "__main__":
    main()
