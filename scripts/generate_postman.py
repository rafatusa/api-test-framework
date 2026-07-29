#!/usr/bin/env python3
"""
Postman Collection Generator
============================
Fetches /openapi.json from the deployed API, then generates a Postman
Collection v2.1 JSON file with:

  - One folder per tag
  - Positive example request per operation (inferred from schema)
  - Negative example request (missing required field / invalid type)
  - Pre-request script for authenticated endpoints (Bearer token from login)
  - Environment variable {{base_url}} for portability

Usage:
    python scripts/generate_postman.py \\
        --base-url http://<IP> \\
        --output reports/postman_collection.json
"""
import argparse
import json
import sys
import uuid
from typing import Any

import requests


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_id() -> str:
    return str(uuid.uuid4())


def _infer_example(schema: dict, negative: bool = False) -> Any:
    """
    Recursively generate an example value from a JSON Schema fragment.
    When negative=True, return an obviously wrong type.
    """
    if not schema:
        return {}

    stype = schema.get("type")
    if "$ref" in schema:
        # caller resolves refs; here we just return a placeholder
        return {} if not negative else None

    if stype == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        result = {}
        for key, prop_schema in props.items():
            if negative and key in required:
                # skip ONE required field to trigger 422
                continue
            result[key] = _infer_example(prop_schema, negative=False)
        return result

    if stype == "array":
        items_schema = schema.get("items", {})
        return [_infer_example(items_schema)]

    if negative:
        return "INVALID_TYPE_STRING" if stype in ("integer", "number", "boolean") else 999

    type_defaults = {
        "string": "example_string",
        "integer": 1,
        "number": 1.0,
        "boolean": True,
        "null": None,
    }
    if stype in type_defaults:
        return type_defaults[stype]

    return "example"


def _resolve_ref(ref: str, components: dict) -> dict:
    """Resolve a $ref like '#/components/schemas/ItemCreate'."""
    parts = ref.lstrip("#/").split("/")
    node = components
    for part in parts[1:]:  # skip 'components'
        node = node.get(part, {})
    return node


def _build_body_examples(operation: dict, components: dict) -> tuple[Any, Any]:
    """Return (positive_example, negative_example) dicts for the request body."""
    rb = operation.get("requestBody", {})
    content = rb.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], components)

    if not schema:
        return None, None

    # Resolve any nested $refs in properties
    resolved_props = {}
    for k, v in schema.get("properties", {}).items():
        if "$ref" in v:
            resolved_props[k] = _resolve_ref(v["$ref"], components)
        else:
            resolved_props[k] = v
    schema["properties"] = resolved_props

    positive = _infer_example(schema, negative=False)
    negative = _infer_example(schema, negative=True)
    return positive, negative


BEARER_PRE_REQUEST = """\
// Obtain a fresh token before this request
const loginRequest = {
    url: pm.environment.get('base_url') + '/auth/token',
    method: 'POST',
    header: {'Content-Type': 'application/json'},
    body: {mode: 'raw', raw: JSON.stringify({
        username: pm.environment.get('username') || 'alice',
        password: pm.environment.get('password') || 'alicepassword123'
    })}
};
pm.sendRequest(loginRequest, function (err, res) {
    pm.environment.set('access_token', res.json().access_token);
});
"""


def _build_item(
    method: str,
    path: str,
    operation: dict,
    components: dict,
    base_url: str,
    label_suffix: str = "",
    negative: bool = False,
) -> dict:
    name = operation.get("summary") or f"{method.upper()} {path}"
    if label_suffix:
        name = f"{name} [{label_suffix}]"

    # Security: check if operation requires a bearer token
    requires_auth = bool(operation.get("security") or [{"BearerToken": []}])
    # Only attach pre-request script when the endpoint has security defined
    security_schemes = components.get("securitySchemes", {})
    op_security = operation.get("security", [])
    needs_auth = bool(op_security) or any(
        "Bearer" in str(op_security) for _ in [0]
    )

    raw_url = f"{{{{base_url}}}}{path}"
    url_obj = {
        "raw": raw_url,
        "host": ["{{base_url}}"],
        "path": [p for p in path.strip("/").split("/") if p],
    }

    headers = [{"key": "Content-Type", "value": "application/json"}]
    if needs_auth:
        headers.append({"key": "Authorization", "value": "Bearer {{access_token}}"})

    body_obj = None
    positive_ex, negative_ex = _build_body_examples(operation, components)
    if method.lower() in ("post", "put", "patch"):
        example = negative_ex if negative else positive_ex
        if example is not None:
            body_obj = {
                "mode": "raw",
                "raw": json.dumps(example, indent=2),
                "options": {"raw": {"language": "json"}},
            }

    # Build test script for status code assertion
    expected_codes = []
    for code_str in operation.get("responses", {}).keys():
        if code_str.isdigit():
            expected_codes.append(int(code_str))
    if negative:
        test_code = 422
        test_script = f"pm.test('Status is 422', () => pm.response.to.have.status(422));"
    elif expected_codes:
        success_codes = [c for c in expected_codes if c < 400]
        test_code = success_codes[0] if success_codes else expected_codes[0]
        test_script = (
            f"pm.test('Status is {test_code}', () => pm.response.to.have.status({test_code}));\n"
            "pm.test('Response is JSON', () => pm.response.to.be.json);"
        )
    else:
        test_script = "pm.test('Status 2xx', () => pm.expect(pm.response.code).to.be.oneOf([200,201,204]));"

    event = [
        {
            "listen": "test",
            "script": {"type": "text/javascript", "exec": test_script.splitlines()},
        }
    ]
    if needs_auth:
        event.insert(0, {
            "listen": "prerequest",
            "script": {"type": "text/javascript", "exec": BEARER_PRE_REQUEST.splitlines()},
        })

    item: dict = {
        "id": _new_id(),
        "name": name,
        "request": {
            "method": method.upper(),
            "header": headers,
            "url": url_obj,
        },
        "event": event,
        "response": [],
    }
    if body_obj:
        item["request"]["body"] = body_obj

    return item


def generate_collection(openapi: dict, base_url: str) -> dict:
    components = openapi.get("components", {})
    paths = openapi.get("paths", {})

    # Group by tag
    folders: dict = {}
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            tags = operation.get("tags", ["default"])
            tag = tags[0]
            if tag not in folders:
                folders[tag] = {"id": _new_id(), "name": tag, "item": []}

            # Positive request
            folders[tag]["item"].append(
                _build_item(method, path, operation, components, base_url, "positive")
            )
            # Negative request (only for POST/PUT/PATCH that have a body)
            if method.lower() in ("post", "put", "patch"):
                folders[tag]["item"].append(
                    _build_item(
                        method, path, operation, components, base_url,
                        "negative — missing required field", negative=True
                    )
                )

    collection = {
        "info": {
            "_postman_id": _new_id(),
            "name": openapi.get("info", {}).get("title", "API Collection"),
            "description": openapi.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": base_url, "type": "string"},
            {"key": "access_token", "value": "", "type": "string"},
            {"key": "username", "value": "alice", "type": "string"},
            {"key": "password", "value": "alicepassword123", "type": "string"},
        ],
        "item": list(folders.values()),
    }
    return collection


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Postman collection from OpenAPI spec")
    parser.add_argument("--base-url", required=True, help="API base URL")
    parser.add_argument("--output", default="reports/postman_collection.json", help="Output path")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    print(f"Fetching OpenAPI schema from {base_url}/openapi.json …")
    try:
        resp = requests.get(f"{base_url}/openapi.json", timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"ERROR: Could not fetch OpenAPI schema: {exc}", file=sys.stderr)
        sys.exit(1)

    openapi = resp.json()
    collection = generate_collection(openapi, base_url)

    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as fh:
        json.dump(collection, fh, indent=2)

    total_requests = sum(len(f["item"]) for f in collection["item"])
    print(f"Generated Postman collection → {args.output}")
    print(f"  Folders : {len(collection['item'])}")
    print(f"  Requests: {total_requests}")


if __name__ == "__main__":
    main()
