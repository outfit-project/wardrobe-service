import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.categories import Category, Style


class ItemUploadedEvent(BaseModel):
    event_type: str = "item.uploaded"
    item_id: uuid.UUID
    user_id: uuid.UUID
    image_url: str


class ClothingItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: Category
    image_url: str

    subcategory: Optional[str] = None
    style: Optional[Style] = Style.UNDEFINED
    color_hex: Optional[str] = None

    embedding: Optional[list[float]] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def set_embedding(self, embedding: list[float]) -> None:
        self.embedding = embedding


class WardrobeResponse(BaseModel):
    items: list[ClothingItem]
    total: int


class UploadClothingItemResponse(BaseModel):
    item_id: str
    image_url: str


class UpdateEmbeddingRequest(BaseModel):
    item_id: uuid.UUID
    embedding: list[float]
    style: str | None = None
    category: str | None = None