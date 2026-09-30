import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_serves_html():
    """Verify that root endpoint serves the HTML frontend."""
    response = client.get("/")
    assert response.status_code == 200
    assert "FinNews AI" in response.text
    assert "text/html" in response.headers.get("content-type", "")

def test_api_info():
    """Verify that /api returns valid metadata."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "FinNews AI – Financial News Simplifier"
    assert "endpoints" in data
    assert "groq_model" in data

def test_health_endpoint():
    """Verify that /health checks configuration and returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "groq_configured" in data
    assert "newsapi_configured" in data
    assert data["model"] == "llama-3.3-70b-versatile"

def test_news_endpoint_default_count():
    """Verify that /news returns 5 articles by default with required simplified fields."""
    response = client.get("/news")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] == 5
    assert len(data["articles"]) == 5

    first = data["articles"][0]
    assert "title" in first
    assert "source" in first
    assert "summary" in first
    assert isinstance(first["key_takeaways"], list)
    assert len(first["key_takeaways"]) > 0

def test_news_endpoint_custom_count():
    """Verify that /news?count=3 returns exactly 3 articles."""
    response = client.get("/news?count=3")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["articles"]) == 3

def test_news_endpoint_count_boundary_one():
    """Verify boundary condition count=1."""
    response = client.get("/news?count=1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["articles"]) == 1

def test_news_endpoint_invalid_count_underflow():
    """Verify that count=0 is rejected with 422 Unprocessable Entity."""
    response = client.get("/news?count=0")
    assert response.status_code == 422

def test_news_endpoint_invalid_count_overflow():
    """Verify that count=15 is rejected with 422 Unprocessable Entity."""
    response = client.get("/news?count=15")
    assert response.status_code == 422

def test_news_endpoint_category_filtering():
    """Verify that topic category parameter is handled properly."""
    response = client.get("/news?count=2&category=Economy")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["articles"]) == 2

def test_cors_headers():
    """Verify CORS headers are returned to allow web clients."""
    origin = "http://localhost:3000"
    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ["*", origin]
