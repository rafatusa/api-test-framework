"""Users router — CRUD on the user store."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.security import hash_password
from app.db import fake_users_db, next_user_id
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
def list_users(_: dict = Depends(get_current_user)) -> List[UserResponse]:
    """List all users (requires authentication)."""
    return [UserResponse(**u) for u in fake_users_db.values()]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate) -> UserResponse:
    """Register a new user."""
    if body.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    new_user = {
        "id": next_user_id(),
        "username": body.username,
        "email": body.email,
        "hashed_password": hash_password(body.password),
        "is_active": True,
        "role": "user",
    }
    fake_users_db[body.username] = new_user
    return UserResponse(**new_user)


@router.get("/{username}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(username: str, _: dict = Depends(get_current_user)) -> UserResponse:
    """Fetch a single user by username (requires authentication)."""
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)


@router.patch("/{username}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(
    username: str,
    body: UserUpdate,
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    """Update a user's email or active status (owner or admin only)."""
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user["username"] != username and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to update this user",
        )
    if body.email is not None:
        user["email"] = body.email
    if body.is_active is not None:
        user["is_active"] = body.is_active
    return UserResponse(**user)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete a user (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    if username not in fake_users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    del fake_users_db[username]
