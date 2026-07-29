"""Authentication and authorization tests."""
import time


class TestLogin:
    # ── Positive ────────────────────────────────────────────────────────────
    def test_login_alice_returns_200(self, client):
        resp = client.post(
            "/auth/token",
            json={"username": "alice", "password": "alicepassword123"},
        )
        assert resp.status_code == 200

    def test_login_response_schema(self, client):
        resp = client.post(
            "/auth/token",
            json={"username": "alice", "password": "alicepassword123"},
        )
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str)
        assert len(body["access_token"]) > 20

    def test_login_bob_returns_200(self, client):
        resp = client.post(
            "/auth/token",
            json={"username": "bob", "password": "bobpassword456"},
        )
        assert resp.status_code == 200

    def test_login_response_time_under_2s(self, client):
        start = time.monotonic()
        client.post(
            "/auth/token",
            json={"username": "alice", "password": "alicepassword123"},
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 2000, f"Login took {elapsed_ms:.0f}ms (limit 2000ms)"

    # ── Negative ────────────────────────────────────────────────────────────
    def test_wrong_password_returns_401(self, client):
        resp = client.post(
            "/auth/token",
            json={"username": "alice", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_unknown_user_returns_401(self, client):
        resp = client.post(
            "/auth/token",
            json={"username": "ghost", "password": "anything"},
        )
        assert resp.status_code == 401

    def test_missing_password_returns_422(self, client):
        resp = client.post("/auth/token", json={"username": "alice"})
        assert resp.status_code == 422

    def test_missing_username_returns_422(self, client):
        resp = client.post("/auth/token", json={"password": "alicepassword123"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/auth/token", json={})
        assert resp.status_code == 422

    def test_wrong_content_type_returns_422(self, client):
        resp = client.post(
            "/auth/token",
            data="username=alice&password=alicepassword123",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 422

    def test_extra_fields_ignored(self, client):
        resp = client.post(
            "/auth/token",
            json={
                "username": "alice",
                "password": "alicepassword123",
                "extra": "ignored",
            },
        )
        assert resp.status_code == 200


class TestGetMe:
    # ── Positive ────────────────────────────────────────────────────────────
    def test_get_me_alice(self, client, alice_headers):
        resp = client.get("/auth/me", headers=alice_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "alice"
        assert body["role"] == "admin"

    def test_get_me_response_schema(self, client, alice_headers):
        resp = client.get("/auth/me", headers=alice_headers)
        body = resp.json()
        required_fields = {"id", "username", "email", "is_active", "role"}
        assert required_fields.issubset(body.keys())

    def test_get_me_no_password_in_response(self, client, alice_headers):
        resp = client.get("/auth/me", headers=alice_headers)
        body = resp.json()
        assert "password" not in body
        assert "hashed_password" not in body

    # ── Negative ────────────────────────────────────────────────────────────
    def test_get_me_no_token_returns_403(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 403

    def test_get_me_invalid_token_returns_403(self, client):
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 403

    def test_get_me_malformed_bearer_returns_403(self, client):
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "NotBearer sometoken"},
        )
        assert resp.status_code == 403

    def test_get_me_empty_bearer_returns_403(self, client):
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 403
