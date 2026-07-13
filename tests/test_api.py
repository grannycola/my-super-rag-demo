"""Tests for FastAPI endpoints."""

import json

from fastapi.testclient import TestClient

from src.api.app import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "vector_store" in data
    assert "retrieval_hit_rate" in data


def test_health_includes_retrieval_hit_rate(tmp_path, monkeypatch):
    report_path = tmp_path / "retrieval_eval.json"
    report_path.write_text(json.dumps({"hit_rate": 0.4}), encoding="utf-8")
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))

    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["retrieval_hit_rate"] == 0.4


def test_ingest_requires_admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    client = TestClient(create_app())

    response = client.post("/ingest", json={"source": "langchain"})
    assert response.status_code == 401

    response = client.post(
        "/ingest",
        json={"source": "langchain"},
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_evaluate_requires_admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")
    client = TestClient(create_app())

    response = client.post("/evaluate")
    assert response.status_code == 401

    response = client.post("/evaluate", headers={"X-Admin-Key": "wrong-key"})
    assert response.status_code == 401


def test_admin_endpoints_disabled_without_key(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    client = TestClient(create_app())

    response = client.post("/ingest", json={"source": "langchain"}, headers={"X-Admin-Key": "any"})
    assert response.status_code == 503

    response = client.post("/evaluate", headers={"X-Admin-Key": "any"})
    assert response.status_code == 503
