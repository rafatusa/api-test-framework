"""Items endpoint tests — CRUD, auth, pagination, negative cases."""
import time


class TestListItems:
    def test_list_items_returns_200(self, client):
        resp = client.get("/items/")
        assert resp.status_code == 200

    def test_list_items_returns_list(self, client):
        resp = client.get("/items/")
        assert isinstance(resp.json(), list)

    def test_list_items_no_auth_required(self, client):
        """Public endpoint — no token needed."""
        resp = client.get("/items/")
        assert resp.status_code == 200

    def test_list_items_schema(self, client):
        resp = client.get("/items/")
        items = resp.json()
        assert len(items) >= 1
        item = items[0]
        assert all(k in item for k in ("id", "title", "price", "owner"))

    def test_list_items_pagination_skip(self, client):
        all_items = client.get("/items/").json()
        skipped = client.get("/items/?skip=1").json()
        assert len(skipped) == max(0, len(all_items) - 1)

    def test_list_items_pagination_limit(self, client):
        resp = client.get("/items/?limit=1")
        assert len(resp.json()) <= 1

    def test_list_items_filter_by_owner(self, client):
        resp = client.get("/items/?owner=alice")
        for item in resp.json():
            assert item["owner"] == "alice"

    def test_list_items_unknown_owner_returns_empty(self, client):
        resp = client.get("/items/?owner=nobody")
        assert resp.json() == []

    def test_list_items_invalid_skip_returns_422(self, client):
        resp = client.get("/items/?skip=-1")
        assert resp.status_code == 422

    def test_list_items_invalid_limit_returns_422(self, client):
        resp = client.get("/items/?limit=0")
        assert resp.status_code == 422

    def test_list_items_limit_over_max_returns_422(self, client):
        resp = client.get("/items/?limit=101")
        assert resp.status_code == 422

    def test_list_items_response_time_under_500ms(self, client):
        start = time.monotonic()
        client.get("/items/")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 500, f"List items took {elapsed_ms:.0f}ms"


class TestGetItem:
    def test_get_existing_item_200(self, client):
        resp = client.get("/items/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_item_schema(self, client):
        resp = client.get("/items/1")
        body = resp.json()
        assert all(k in body for k in ("id", "title", "description", "price", "owner"))

    def test_get_nonexistent_item_404(self, client):
        resp = client.get("/items/99999")
        assert resp.status_code == 404

    def test_get_item_invalid_id_returns_422(self, client):
        resp = client.get("/items/not-an-int")
        assert resp.status_code == 422


class TestCreateItem:
    def test_create_item_returns_201(self, client, alice_headers):
        payload = {"title": "Test Widget", "description": "A test item", "price": 4.99}
        resp = client.post("/items/", json=payload, headers=alice_headers)
        assert resp.status_code == 201

    def test_create_item_response_schema(self, client, alice_headers):
        payload = {"title": "Schema Widget", "price": 1.00}
        resp = client.post("/items/", json=payload, headers=alice_headers)
        body = resp.json()
        assert all(k in body for k in ("id", "title", "price", "owner"))
        assert body["owner"] == "alice"

    def test_create_item_no_auth_returns_403(self, client):
        payload = {"title": "Unauth Item", "price": 1.00}
        resp = client.post("/items/", json=payload)
        assert resp.status_code == 403

    def test_create_item_missing_price_returns_422(self, client, alice_headers):
        resp = client.post("/items/", json={"title": "No Price"}, headers=alice_headers)
        assert resp.status_code == 422

    def test_create_item_missing_title_returns_422(self, client, alice_headers):
        resp = client.post("/items/", json={"price": 5.00}, headers=alice_headers)
        assert resp.status_code == 422

    def test_create_item_empty_title_returns_422(self, client, alice_headers):
        resp = client.post(
            "/items/",
            json={"title": "  ", "price": 5.00},
            headers=alice_headers,
        )
        assert resp.status_code == 422

    def test_create_item_negative_price_returns_422(self, client, alice_headers):
        resp = client.post(
            "/items/",
            json={"title": "Bad", "price": -1.00},
            headers=alice_headers,
        )
        assert resp.status_code == 422

    def test_create_item_title_too_long_returns_422(self, client, alice_headers):
        resp = client.post(
            "/items/",
            json={"title": "x" * 101, "price": 1.00},
            headers=alice_headers,
        )
        assert resp.status_code == 422

    def test_create_item_empty_body_returns_422(self, client, alice_headers):
        resp = client.post("/items/", json={}, headers=alice_headers)
        assert resp.status_code == 422

    def test_create_item_response_time_under_500ms(self, client, alice_headers):
        start = time.monotonic()
        client.post(
            "/items/",
            json={"title": "Perf Item", "price": 1.00},
            headers=alice_headers,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms < 500, f"Create item took {elapsed_ms:.0f}ms"


class TestUpdateItem:
    def test_owner_can_update_own_item(self, client, alice_headers):
        resp = client.patch(
            "/items/1",
            json={"title": "Updated Title"},
            headers=alice_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_non_owner_cannot_update_returns_403(self, client, bob_headers):
        resp = client.patch(
            "/items/1",
            json={"title": "Bob hijack"},
            headers=bob_headers,
        )
        assert resp.status_code == 403

    def test_update_nonexistent_item_returns_404(self, client, alice_headers):
        resp = client.patch(
            "/items/99999",
            json={"title": "Ghost"},
            headers=alice_headers,
        )
        assert resp.status_code == 404

    def test_update_no_auth_returns_403(self, client):
        resp = client.patch("/items/1", json={"title": "Unauth"})
        assert resp.status_code == 403


class TestDeleteItem:
    def test_owner_can_delete_own_item(self, client, alice_headers):
        create_resp = client.post(
            "/items/",
            json={"title": "To Delete", "price": 0.01},
            headers=alice_headers,
        )
        item_id = create_resp.json()["id"]
        delete_resp = client.delete(f"/items/{item_id}", headers=alice_headers)
        assert delete_resp.status_code == 204

    def test_non_owner_cannot_delete_returns_403(self, client, bob_headers):
        resp = client.delete("/items/1", headers=bob_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent_returns_404(self, client, alice_headers):
        resp = client.delete("/items/99999", headers=alice_headers)
        assert resp.status_code == 404

    def test_delete_no_auth_returns_403(self, client):
        resp = client.delete("/items/1")
        assert resp.status_code == 403
