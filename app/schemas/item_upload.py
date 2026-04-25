import uuid
from typing import Optional

from pydantic import BaseModel

from app.schemas.categories import Category, Style


class ItemUploadedEvent(BaseModel):
    item_id: uuid.UUID
    user_id: uuid.UUID
    image_url: str


class ClothingItem:
    user_id: uuid.UUID
    item_id: uuid.UUID
    image_url: str

    embedding: Optional[list[float]] = None

    category: Category
    subcategory: Optional[str] = None
    style: Style.UNDEFINED
    color_hex: Optional[str] = None

    def get_embedding(self, embedding: list[float]) -> None:
        self.embedding = embedding
