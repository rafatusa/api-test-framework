"""Health endpoint tests — liveness, schema, response time."""
import time


class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_schema(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert "status" in body
        assert body["status"] == "ok"
        assert "version" in body

    def test_health_response_time_under_500ms(self, client):
        start = time.monotonic()
        client.get("/health")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 500, f"Health check took {elapsed_ms:.0f}ms (limit 500ms)"

    def test_health_content_type_json(self, client):
        resp = client.get("/health")
        assert "application/json" in resp.headers.get("content-type", "")
