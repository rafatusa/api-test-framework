"""In-memory data stores (no external DB — keeps the demo self-contained)."""
from app.core.security import hash_password

# Keyed by username
fake_users_db: dict = {
    "alice": {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "hashed_password": hash_password("alicepassword123"),
        "is_active": True,
        "role": "admin",
    },
    "bob": {
        "id": 2,
        "username": "bob",
        "email": "bob@example.com",
        "hashed_password": hash_password("bobpassword456"),
        "is_active": True,
        "role": "user",
    },
}

# Keyed by item id
fake_items_db: dict = {
    1: {"id": 1, "title": "Item One", "description": "First item", "price": 9.99, "owner": "alice"},
    2: {"id": 2, "title": "Item Two", "description": "Second item", "price": 19.99, "owner": "bob"},
}

_next_item_id: int = 3
_next_user_id: int = 3


def next_item_id() -> int:
    global _next_item_id
    val = _next_item_id
    _next_item_id += 1
    return val


def next_user_id() -> int:
    global _next_user_id
    val = _next_user_id
    _next_user_id += 1
    return val
