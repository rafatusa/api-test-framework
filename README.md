# API Test Framework

A production-ready FastAPI service on AWS EC2 with a **complete automated API testing framework** — endpoint discovery, positive/negative test suites, schema validation, auth/authz tests, Postman collection generation, and HTML + Markdown reports.

---

## Architecture

```
Client → nginx (EC2 :80) → Uvicorn/FastAPI (:8000)
                                   │
                         ┌─────────┴──────────┐
                     /items/             /users/
                     /auth/token         /auth/me
                     /health             /openapi.json
```

See `.udap/architecture.d2` for the full diagram.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | — | Liveness probe |
| GET | `/openapi.json` | — | OpenAPI spec (used by Postman generator) |
| GET | `/docs` | — | Swagger UI |
| POST | `/auth/token` | — | Login → JWT |
| GET | `/auth/me` | Bearer | Current user profile |
| GET | `/items/` | — | List items (paginated) |
| POST | `/items/` | Bearer | Create item |
| GET | `/items/{id}` | — | Get item |
| PATCH | `/items/{id}` | Bearer | Update item (owner/admin) |
| DELETE | `/items/{id}` | Bearer | Delete item (owner/admin) |
| GET | `/users/` | Bearer | List users |
| POST | `/users/` | — | Register user |
| GET | `/users/{username}` | Bearer | Get user |
| PATCH | `/users/{username}` | Bearer | Update user (self/admin) |
| DELETE | `/users/{username}` | Bearer | Delete user (admin only) |

**Seed credentials** (in-memory, reset on restart):
- `alice` / `alicepassword123` — role: admin
- `bob` / `bobpassword456` — role: user

---

## Local Development

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Open http://localhost:8000
```

### Run unit tests locally

```bash
pip install -r requirements-test.txt
pytest tests/unit/ -v
```

### Run API tests locally (against local server)

```bash
# In one terminal:
uvicorn app.main:app

# In another:
pytest tests/api/ -v \
  --html=reports/test-report.html --self-contained-html \
  --md-report --md-report-output=reports/test-report.md
```

### Generate Postman collection locally

```bash
python scripts/generate_postman.py --base-url http://localhost:8000 \
  --output reports/postman_collection.json
```

---

## CI/CD Pipeline

| Stage | What it does |
|-------|--------------|
| `lint` | flake8 + black + isort |
| `test` | pytest unit tests |
| `provision` | Terraform → EC2 + EIP + SG |
| `configure` | Ansible → nginx + systemd + venv |
| `verify` | `/health` curl with retries |
| `api_tests` | Full API test suite + Postman export |

Artifacts uploaded after `api_tests`:
- `reports/test-report.html` — self-contained HTML report
- `reports/test-report.md` — Markdown report
- `reports/postman_collection.json` — Postman v2.1 collection

---

## Test Suite Structure

```
tests/
  unit/
    test_security.py       # JWT + bcrypt unit tests
    test_schemas.py        # Pydantic schema validation
  api/
    conftest.py            # base_url fixture, auth token fixtures
    test_health.py         # /health endpoint
    test_auth.py           # login, /me, invalid tokens
    test_items.py          # items CRUD, auth, pagination
    test_users.py          # users CRUD, roles, auth
    test_schema_validation.py  # OpenAPI spec + response compliance
    test_negative.py       # invalid payloads, missing fields, injections
    test_status_codes.py   # status code contract for every endpoint
    test_response_times.py # p95 latency thresholds
```

---

## Configuration

| Variable | Where | Description |
|----------|-------|-------------|
| `JWT_SECRET_KEY` | CI secret → `/opt/app/.env` | JWT signing key (set via `set_pipeline_secret`) |

---

## Operations

```bash
# Check service status
ssh -i deploy_key ubuntu@<IP> 'sudo systemctl status app'

# Tail application logs
ssh -i deploy_key ubuntu@<IP> 'sudo journalctl -u app -f'

# Restart service
ssh -i deploy_key ubuntu@<IP> 'sudo systemctl restart app'

# Restart nginx
ssh -i deploy_key ubuntu@<IP> 'sudo systemctl restart nginx'
```

**Destroy infrastructure:**
Trigger the `destroy` workflow in GitHub Actions.
