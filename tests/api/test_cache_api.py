from fastapi.testclient import TestClient
from main import app
from infrastructure.cache import cache

client = TestClient(app)


def test_clear_cache_returns_200():
    response = client.post("/cache/clear")
    assert response.status_code == 200
    assert response.json() == {"message": "Cache cleared"}


def test_clear_cache_actually_clears():
    cache.set("key", "value")
    client.post("/cache/clear")
    assert cache.get("key") is None
