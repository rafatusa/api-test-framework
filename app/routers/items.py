"""Items router — CRUD on the items store."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.db import fake_items_db, next_item_id
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate

router = APIRouter()


@router.get("/", response_model=List[ItemResponse], status_code=status.HTTP_200_OK)
def list_items(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max items to return"),
    owner: Optional[str] = Query(default=None, description="Filter by owner username"),
) -> List[ItemResponse]:
    """List items with optional pagination and owner filter. No auth required."""
    items = list(fake_items_db.values())
    if owner:
        items = [i for i in items if i["owner"] == owner]
    return [ItemResponse(**i) for i in items[skip: skip + limit]]


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    body: ItemCreate,
    current_user: dict = Depends(get_current_user),
) -> ItemResponse:
    """Create a new item (requires authentication)."""
    item_id = next_item_id()
    new_item = {
        "id": item_id,
        "title": body.title,
        "description": body.description,
        "price": body.price,
        "owner": current_user["username"],
    }
    fake_items_db[item_id] = new_item
    return ItemResponse(**new_item)


@router.get("/{item_id}", response_model=ItemResponse, status_code=status.HTTP_200_OK)
def get_item(item_id: int) -> ItemResponse:
    """Fetch a single item by ID. No auth required."""
    item = fake_items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return ItemResponse(**item)


@router.patch("/{item_id}", response_model=ItemResponse, status_code=status.HTTP_200_OK)
def update_item(
    item_id: int,
    body: ItemUpdate,
    current_user: dict = Depends(get_current_user),
) -> ItemResponse:
    """Update an item (owner or admin only)."""
    item = fake_items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to update this item",
        )
    if body.title is not None:
        item["title"] = body.title
    if body.description is not None:
        item["description"] = body.description
    if body.price is not None:
        item["price"] = body.price
    return ItemResponse(**item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete an item (owner or admin only)."""
    item = fake_items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item["owner"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to delete this item",
        )
    del fake_items_db[item_id]
