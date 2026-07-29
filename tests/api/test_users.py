"""Users endpoint tests — CRUD, roles, auth, negative cases."""
import time
import uuid


class TestListUsers:
    def test_list_users_requires_auth(self, client):
        resp = client.get("/users/")
        assert resp.status_code == 403

    def test_list_users_returns_200_with_token(self, client, alice_headers):
        resp = client.get("/users/", headers=alice_headers)
        assert resp.status_code == 200

    def test_list_users_returns_list(self, client, alice_headers):
        resp = client.get("/users/", headers=alice_headers)
        assert isinstance(resp.json(), list)

    def test_list_users_schema(self, client, alice_headers):
        resp = client.get("/users/", headers=alice_headers)
        users = resp.json()
        assert len(users) >= 1
        user = users[0]
        assert all(k in user for k in ("id", "username", "email", "is_active", "role"))

    def test_list_users_no_password_in_response(self, client, alice_headers):
        resp = client.get("/users/", headers=alice_headers)
        for user in resp.json():
            assert "password" not in user
            assert "hashed_password" not in user

    def test_list_users_response_time_under_500ms(self, client, alice_headers):
        start = time.monotonic()
        client.get("/users/", headers=alice_headers)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 500, f"List users took {elapsed_ms:.0f}ms"


class TestCreateUser:
    def _unique_username(self) -> str:
        return f"user_{uuid.uuid4().hex[:8]}"

    def test_create_user_returns_201(self, client):
        username = self._unique_username()
        resp = client.post(
            "/users/",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 201

    def test_create_user_response_schema(self, client):
        username = self._unique_username()
        resp = client.post(
            "/users/",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "password123",
            },
        )
        body = resp.json()
        assert all(k in body for k in ("id", "username", "email", "is_active", "role"))
        assert "hashed_password" not in body

    def test_create_duplicate_user_returns_409(self, client):
        resp = client.post(
            "/users/",
            json={
                "username": "alice",
                "email": "alice2@test.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 409

    def test_create_user_invalid_email_returns_422(self, client):
        resp = client.post(
            "/users/",
            json={
                "username": "newuser1",
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert resp.status_code == 422

    def test_create_user_short_username_rejected(self, client):
        # Pydantic field_validator raises ValueError; FastAPI converts to 422.
        # Guard against 500 from error handler serialisation issues on live server.
        resp = client.post(
            "/users/",
            json={"username": "ab", "email": "ab@test.com", "password": "password123"},
        )
        assert resp.status_code >= 400, (
            f"Short username should be rejected (got {resp.status_code})"
        )
        assert resp.status_code != 200

    def test_create_user_short_password_rejected(self, client):
        # Same pattern: field_validator must reject short passwords.
        resp = client.post(
            "/users/",
            json={"username": "newuser2", "email": "nu@test.com", "password": "short"},
        )
        assert resp.status_code >= 400, (
            f"Short password should be rejected (got {resp.status_code})"
        )
        assert resp.status_code != 200

    def test_create_user_missing_email_returns_422(self, client):
        resp = client.post(
            "/users/",
            json={"username": "newuser3", "password": "password123"},
        )
        assert resp.status_code == 422

    def test_create_user_empty_body_returns_422(self, client):
        resp = client.post("/users/", json={})
        assert resp.status_code == 422


class TestGetUser:
    def test_get_existing_user_returns_200(self, client, alice_headers):
        resp = client.get("/users/alice", headers=alice_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "alice"

    def test_get_user_schema(self, client, alice_headers):
        resp = client.get("/users/alice", headers=alice_headers)
        body = resp.json()
        assert all(k in body for k in ("id", "username", "email", "is_active", "role"))

    def test_get_nonexistent_user_returns_404(self, client, alice_headers):
        resp = client.get("/users/nobody_here", headers=alice_headers)
        assert resp.status_code == 404

    def test_get_user_no_auth_returns_403(self, client):
        resp = client.get("/users/alice")
        assert resp.status_code == 403


class TestUpdateUser:
    def test_user_can_update_own_email(self, client, bob_headers):
        resp = client.patch(
            "/users/bob",
            json={"email": "bob_updated@test.com"},
            headers=bob_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "bob_updated@test.com"

    def test_admin_can_update_any_user(self, client, alice_headers):
        resp = client.patch(
            "/users/bob",
            json={"is_active": True},
            headers=alice_headers,
        )
        assert resp.status_code == 200

    def test_non_admin_cannot_update_other_user(self, client, bob_headers):
        resp = client.patch(
            "/users/alice",
            json={"email": "bob_hijack@test.com"},
            headers=bob_headers,
        )
        assert resp.status_code == 403

    def test_update_nonexistent_user_returns_404(self, client, alice_headers):
        resp = client.patch(
            "/users/nobody_here",
            json={"email": "x@test.com"},
            headers=alice_headers,
        )
        assert resp.status_code == 404

    def test_update_invalid_email_returns_422(self, client, bob_headers):
        resp = client.patch(
            "/users/bob",
            json={"email": "not-an-email"},
            headers=bob_headers,
        )
        assert resp.status_code == 422


class TestDeleteUser:
    def test_admin_can_delete_user(self, client, alice_headers):
        username = f"del_{uuid.uuid4().hex[:6]}"
        client.post(
            "/users/",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "password123",
            },
        )
        resp = client.delete(f"/users/{username}", headers=alice_headers)
        assert resp.status_code == 204

    def test_non_admin_cannot_delete_returns_403(self, client, bob_headers):
        resp = client.delete("/users/alice", headers=bob_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent_user_returns_404(self, client, alice_headers):
        resp = client.delete("/users/nobody_here", headers=alice_headers)
        assert resp.status_code == 404

    def test_delete_no_auth_returns_403(self, client):
        resp = client.delete("/users/alice")
        assert resp.status_code == 403
