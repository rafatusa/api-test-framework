"""Item Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel, field_validator


class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty")
        if len(v) > 100:
            raise ValueError("Title must be 100 characters or fewer")
        return v

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v


class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: float
    owner: str


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
