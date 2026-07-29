"""
HTTP status code contract tests.

These tests verify that every endpoint returns the documented status code
for both success and error paths — no surprises in the status code layer.
"""


class TestSuccessStatusCodes:
    def test_health_get_is_200(self, client):
        assert client.get("/health").status_code == 200

    def test_openapi_get_is_200(self, client):
        assert client.get("/openapi.json").status_code == 200

    def test_auth_token_post_is_200(self, client):
        resp = client.post("/auth/token", json={"username": "alice", "password": "alicepassword123"})
        assert resp.status_code == 200

    def test_auth_me_get_is_200(self, client, alice_headers):
        assert client.get("/auth/me", headers=alice_headers).status_code == 200

    def test_users_list_is_200(self, client, alice_headers):
        assert client.get("/users/", headers=alice_headers).status_code == 200

    def test_users_create_is_201(self, client):
        import uuid
        username = f"sc_{uuid.uuid4().hex[:6]}"
        resp = client.post(
            "/users/",
            json={"username": username, "email": f"{username}@test.com", "password": "password123"},
        )
        assert resp.status_code == 201

    def test_users_get_is_200(self, client, alice_headers):
        assert client.get("/users/alice", headers=alice_headers).status_code == 200

    def test_items_list_is_200(self, client):
        assert client.get("/items/").status_code == 200

    def test_items_get_is_200(self, client):
        assert client.get("/items/1").status_code == 200

    def test_items_create_is_201(self, client, alice_headers):
        resp = client.post(
            "/items/", json={"title": "SC Test Item", "price": 1.0}, headers=alice_headers
        )
        assert resp.status_code == 201

    def test_items_delete_is_204(self, client, alice_headers):
        create = client.post(
            "/items/", json={"title": "To Delete SC", "price": 0.1}, headers=alice_headers
        )
        item_id = create.json()["id"]
        resp = client.delete(f"/items/{item_id}", headers=alice_headers)
        assert resp.status_code == 204


class TestClientErrorStatusCodes:
    def test_wrong_login_is_401(self, client):
        resp = client.post("/auth/token", json={"username": "alice", "password": "wrong"})
        assert resp.status_code == 401

    def test_missing_token_is_403(self, client):
        assert client.get("/auth/me").status_code == 403

    def test_invalid_token_is_403(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer bad.token"})
        assert resp.status_code == 403

    def test_nonexistent_item_is_404(self, client):
        assert client.get("/items/99999").status_code == 404

    def test_nonexistent_user_is_404(self, client, alice_headers):
        resp = client.get("/users/no_such_user", headers=alice_headers)
        assert resp.status_code == 404

    def test_duplicate_user_is_409(self, client):
        resp = client.post(
            "/users/",
            json={"username": "alice", "email": "a2@test.com", "password": "password123"},
        )
        assert resp.status_code == 409

    def test_missing_required_field_is_422(self, client, alice_headers):
        resp = client.post("/items/", json={"title": "No price"}, headers=alice_headers)
        assert resp.status_code == 422

    def test_invalid_path_param_type_is_422(self, client):
        assert client.get("/items/not-a-number").status_code == 422

    def test_forbidden_update_is_403(self, client, bob_headers):
        resp = client.patch("/items/1", json={"title": "Bob hijack"}, headers=bob_headers)
        assert resp.status_code == 403

    def test_forbidden_delete_is_403(self, client, bob_headers):
        resp = client.delete("/items/1", headers=bob_headers)
        assert resp.status_code == 403

    def test_non_admin_delete_user_is_403(self, client, bob_headers):
        resp = client.delete("/users/alice", headers=bob_headers)
        assert resp.status_code == 403

    def test_unknown_route_is_404(self, client):
        assert client.get("/this/does/not/exist").status_code == 404
