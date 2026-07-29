"""Unit tests for JWT token creation, verification, and password hashing."""
import pytest
import jwt

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import JWT_ALGORITHM


class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"

    def test_verify_correct_password(self):
        hashed = hash_password("correct123")
        assert verify_password("correct123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct123")
        assert verify_password("wrong456", hashed) is False

    def test_same_password_different_hash(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        # bcrypt salts: hashes differ even for same input
        assert h1 != h2


class TestJWTTokens:
    def test_create_token_returns_string(self):
        token = create_access_token("alice")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_token_subject(self):
        token = create_access_token("alice")
        payload = decode_access_token(token)
        assert payload["sub"] == "alice"

    def test_invalid_token_raises(self):
        with pytest.raises(jwt.PyJWTError):
            decode_access_token("this.is.not.valid")

    def test_tampered_token_raises(self):
        token = create_access_token("alice")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(tampered)

    def test_wrong_secret_raises(self):
        token = jwt.encode({"sub": "alice"}, "wrong-secret", algorithm=JWT_ALGORITHM)
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(token)
