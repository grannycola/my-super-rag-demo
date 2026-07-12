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
