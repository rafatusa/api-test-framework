"""Application configuration — reads from environment variables."""
import os

JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = 60
