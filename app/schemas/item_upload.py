import datetime
import uuid
from dataclasses import field, dataclass
from typing import Optional

from pydantic import BaseModel

from app.schemas.categories import Category, Style


class ItemUploadedEvent(BaseModel):
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

    created_at: datetime = field(default_factory=datetime.utcnow)

    def set_embedding(self, embedding: list[float]) -> None:
        self.embedding = embedding

