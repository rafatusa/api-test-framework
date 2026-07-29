"""Auth router — JWT login and current-user endpoint."""
from fastapi import APIRouter, HTTPException, status, Depends

from app.core.security import create_access_token, verify_password
from app.core.deps import get_current_user
from app.db import fake_users_db
from app.schemas.auth import TokenRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(body: TokenRequest) -> TokenResponse:
    """Exchange username + password for a JWT access token."""
    user = fake_users_db.get(body.username)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=body.username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse(**current_user)
