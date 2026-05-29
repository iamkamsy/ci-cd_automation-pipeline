import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ["TESTING"] = "true"

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_status_code(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_json_body(client):
    response = client.get("/health")
    assert response.get_json() == {"status": "ok"}
