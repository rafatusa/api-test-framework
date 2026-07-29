from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_home_serves_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text
