"""
Response time tests.

Thresholds:
  - Read endpoints   < 500 ms
  - Write endpoints  < 1000 ms
  - Auth endpoints   < 2000 ms  (bcrypt is intentionally slow)
  - p95 over 5 requests: same thresholds

All times measured wall-clock on the CI runner (allow ample margin for
network latency to the EC2 instance).
"""
import time

THRESHOLD_READ_MS = 500
THRESHOLD_WRITE_MS = 1000
THRESHOLD_AUTH_MS = 2000
REPEAT = 5


def _elapsed_ms(fn) -> float:
    start = time.monotonic()
    fn()
    return (time.monotonic() - start) * 1000


def _p95(timings: list) -> float:
    sorted_t = sorted(timings)
    idx = int(len(sorted_t) * 0.95)
    return sorted_t[min(idx, len(sorted_t) - 1)]


class TestReadResponseTimes:
    def test_health_single_call(self, client):
        ms = _elapsed_ms(lambda: client.get("/health"))
        assert ms < THRESHOLD_READ_MS, f"/health took {ms:.0f}ms"

    def test_health_p95_over_5_calls(self, client):
        timings = [_elapsed_ms(lambda: client.get("/health")) for _ in range(REPEAT)]
        p95 = _p95(timings)
        assert p95 < THRESHOLD_READ_MS, f"/health p95={p95:.0f}ms"

    def test_list_items_single_call(self, client):
        ms = _elapsed_ms(lambda: client.get("/items/"))
        assert ms < THRESHOLD_READ_MS, f"GET /items/ took {ms:.0f}ms"

    def test_list_items_p95(self, client):
        timings = [_elapsed_ms(lambda: client.get("/items/")) for _ in range(REPEAT)]
        assert _p95(timings) < THRESHOLD_READ_MS

    def test_get_item_single_call(self, client):
        ms = _elapsed_ms(lambda: client.get("/items/1"))
        assert ms < THRESHOLD_READ_MS, f"GET /items/1 took {ms:.0f}ms"

    def test_openapi_schema_single_call(self, client):
        ms = _elapsed_ms(lambda: client.get("/openapi.json"))
        assert ms < THRESHOLD_READ_MS, f"GET /openapi.json took {ms:.0f}ms"


class TestWriteResponseTimes:
    def test_create_item_single_call(self, client, alice_headers):
        ms = _elapsed_ms(
            lambda: client.post(
                "/items/",
                json={"title": "Perf create", "price": 1.0},
                headers=alice_headers,
            )
        )
        assert ms < THRESHOLD_WRITE_MS, f"POST /items/ took {ms:.0f}ms"

    def test_update_item_single_call(self, client, alice_headers):
        ms = _elapsed_ms(
            lambda: client.patch(
                "/items/1",
                json={"title": "Perf update"},
                headers=alice_headers,
            )
        )
        assert ms < THRESHOLD_WRITE_MS, f"PATCH /items/1 took {ms:.0f}ms"

    def test_create_item_p95(self, client, alice_headers):
        timings = [
            _elapsed_ms(
                lambda: client.post(
                    "/items/",
                    json={"title": "Perf p95", "price": 1.0},
                    headers=alice_headers,
                )
            )
            for _ in range(REPEAT)
        ]
        assert _p95(timings) < THRESHOLD_WRITE_MS


class TestAuthResponseTimes:
    def test_login_single_call(self, client):
        ms = _elapsed_ms(
            lambda: client.post(
                "/auth/token",
                json={"username": "alice", "password": "alicepassword123"},
            )
        )
        assert ms < THRESHOLD_AUTH_MS, f"POST /auth/token took {ms:.0f}ms"

    def test_login_p95_over_5_calls(self, client):
        timings = [
            _elapsed_ms(
                lambda: client.post(
                    "/auth/token",
                    json={"username": "alice", "password": "alicepassword123"},
                )
            )
            for _ in range(REPEAT)
        ]
        p95 = _p95(timings)
        assert p95 < THRESHOLD_AUTH_MS, f"Login p95={p95:.0f}ms"

    def test_get_me_single_call(self, client, alice_headers):
        ms = _elapsed_ms(lambda: client.get("/auth/me", headers=alice_headers))
        assert ms < THRESHOLD_READ_MS, f"GET /auth/me took {ms:.0f}ms"
