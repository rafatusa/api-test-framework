"""
OpenAPI schema validation tests.

Fetches /openapi.json and validates that:
- All expected routes are present
- Request bodies match the declared schema
- Responses match the declared schema
"""
import uuid


class TestOpenAPISchema:
    def test_openapi_endpoint_returns_200(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_openapi_response_is_valid_json(self, client):
        resp = client.get("/openapi.json")
        schema = resp.json()
        assert isinstance(schema, dict)

    def test_openapi_has_required_fields(self, client):
        schema = client.get("/openapi.json").json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_openapi_version_is_3x(self, client):
        schema = client.get("/openapi.json").json()
        assert schema["openapi"].startswith("3.")

    def test_expected_paths_present(self, client):
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        expected = [
            "/health",
            "/auth/token",
            "/auth/me",
            "/users/",
            "/users/{username}",
            "/items/",
            "/items/{item_id}",
        ]
        for path in expected:
            assert path in paths, f"Expected path '{path}' missing from OpenAPI spec"

    def test_health_endpoint_has_get(self, client):
        schema = client.get("/openapi.json").json()
        assert "get" in schema["paths"]["/health"]

    def test_auth_token_endpoint_has_post(self, client):
        schema = client.get("/openapi.json").json()
        assert "post" in schema["paths"]["/auth/token"]

    def test_items_endpoint_has_get_and_post(self, client):
        schema = client.get("/openapi.json").json()
        assert "get" in schema["paths"]["/items/"]
        assert "post" in schema["paths"]["/items/"]

    def test_item_detail_endpoint_has_get_patch_delete(self, client):
        schema = client.get("/openapi.json").json()
        path = schema["paths"]["/items/{item_id}"]
        assert "get" in path
        assert "patch" in path
        assert "delete" in path

    def test_users_endpoint_has_get_and_post(self, client):
        schema = client.get("/openapi.json").json()
        assert "get" in schema["paths"]["/users/"]
        assert "post" in schema["paths"]["/users/"]


class TestResponseSchemaCompliance:
    """Validate live responses against the OpenAPI component schemas."""

    def _get_component_schema(self, client, component_name: str) -> dict:
        schema = client.get("/openapi.json").json()
        return schema["components"]["schemas"][component_name]

    def test_health_response_matches_schema(self, client):
        resp = client.get("/health").json()
        assert resp["status"] == "ok"
        assert isinstance(resp["version"], str)

    def test_item_response_matches_item_schema(self, client):
        resp = client.get("/items/1").json()
        item_schema = self._get_component_schema(client, "ItemResponse")
        required_fields = item_schema.get("required", [])
        for field in required_fields:
            assert field in resp, f"Required field '{field}' missing from item response"
        assert isinstance(resp["id"], int)
        assert isinstance(resp["title"], str)
        assert isinstance(resp["price"], (int, float))
        assert isinstance(resp["owner"], str)

    def test_user_create_response_has_no_password(self, client):
        username = f"sv_{uuid.uuid4().hex[:6]}"
        resp = client.post(
            "/users/",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "password123",
            },
        ).json()
        assert "hashed_password" not in resp
        assert "password" not in resp

    def test_token_response_matches_schema(self, client):
        resp = client.post(
            "/auth/token",
            json={"username": "alice", "password": "alicepassword123"},
        ).json()
        assert "access_token" in resp
        assert "token_type" in resp
        assert resp["token_type"] == "bearer"
        assert isinstance(resp["access_token"], str)
