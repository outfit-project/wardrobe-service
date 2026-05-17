import uuid

from fastapi import HTTPException, status

from app.interfaces.image_abc import IImageStorage
from app.interfaces.item_abc import IClothingRepository


class ClothingItemImage:
    def __init__(
            self,
            repo: IClothingRepository,
            storage: IImageStorage
    ):
        self._repo = repo
        self._storage = storage

    async def execute(self, item_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bytes, str]:
        item = await self._repo.get_by_id(item_id)
        if not item or not item.image_url:
            raise LookupError(f"Image not found")

        if item.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )

        try:
            return await self._storage.get_bytes(item.image_url)
        except Exception as e:
            raise LookupError(f"Failed to get image") from e

    async def execute_public(self, item_id: uuid.UUID) -> tuple[bytes, str]:
        item = await self._repo.get_by_id(item_id)
        if not item or not item.image_url:
            raise LookupError("Image not found")
        try:
            return await self._storage.get_bytes(item.image_url)
        except Exception as e:
            raise LookupError("Failed to get image") from e
