"""Unit tests for Pydantic schema validation."""
import pytest
from pydantic import ValidationError

from app.schemas.item import ItemCreate
from app.schemas.user import UserCreate
from app.schemas.auth import TokenRequest

# Test credential constants — not real secrets, used only in schema validation tests
VALID_PASS = "validpassword99"
SHORT_PASS = "short"


class TestItemCreateSchema:
    def test_valid_item(self):
        item = ItemCreate(title="Widget", price=9.99)
        assert item.title == "Widget"
        assert item.price == 9.99
        assert item.description is None

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError):
            ItemCreate(title="   ", price=5.0)

    def test_title_too_long_raises(self):
        with pytest.raises(ValidationError):
            ItemCreate(title="x" * 101, price=5.0)

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError):
            ItemCreate(title="Widget", price=-1.0)

    def test_zero_price_allowed(self):
        item = ItemCreate(title="Free", price=0.0)
        assert item.price == 0.0

    def test_missing_price_raises(self):
        with pytest.raises(ValidationError):
            ItemCreate(title="Widget")

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ItemCreate(price=5.0)


class TestUserCreateSchema:
    def test_valid_user(self):
        user = UserCreate(username="alice", email="alice@example.com", password=VALID_PASS)
        assert user.username == "alice"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="not-an-email", password=VALID_PASS)

    def test_short_username_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", email="a@b.com", password=VALID_PASS)

    def test_short_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="a@b.com", password=SHORT_PASS)

    def test_missing_fields_raise(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice")


class TestTokenRequestSchema:
    def test_valid_token_request(self):
        req = TokenRequest(username="alice", password=VALID_PASS)
        assert req.username == "alice"

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            TokenRequest(password=VALID_PASS)

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            TokenRequest(username="alice")
