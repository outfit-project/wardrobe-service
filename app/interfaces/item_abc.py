import uuid
from typing import Protocol

from app.schemas.item_upload import ClothingItem


class IClothingRepository(Protocol):
    async def save(self, item: ClothingItem) -> None:
        pass

    async def get_by_id(self, item_id: uuid.UUID) -> ClothingItem:
        pass

    async def list_by_user(self, user_id: uuid.UUID) -> list[ClothingItem]:
        pass

    async def update_embedding(self, item_id: uuid.UUID, embedding: list[float]) -> None:
        pass
