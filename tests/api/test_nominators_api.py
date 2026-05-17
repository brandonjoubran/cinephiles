from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_generate_nominators_returns_200():
    with patch(
        "service.nominators_service.generate_nominators",
        return_value=("dune-part-two", ["bjoubs", "kingkrab", "geomod"]),
    ):
        response = client.get("/nominators/generate")

    assert response.status_code == 200
    assert response.json() == {
        "movie_slug": "dune-part-two",
        "nominators": ["bjoubs", "kingkrab", "geomod"],
    }
