"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from src.api.app import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "vector_store" in data


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
