#!/usr/bin/env bash
# Generate retrieval eval report and copy to frontend/metrics.json
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOP_K="${1:-5}"

echo "==> Running retrieval eval (top_k=${TOP_K})..."

if docker compose ps api --status running -q 2>/dev/null | grep -q .; then
  docker compose exec -T api python -m src.evaluate_retrieval --top-k "$TOP_K"
else
  python -m src.evaluate_retrieval --top-k "$TOP_K"
fi

cp reports/retrieval_eval.json frontend/metrics.json
echo "==> Wrote frontend/metrics.json (hit_rate=$(python -c "import json; print(json.load(open('frontend/metrics.json'))['hit_rate'])"))"
