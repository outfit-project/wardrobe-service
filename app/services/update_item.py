import uuid

from fastapi import HTTPException, status

from app.interfaces.item_abc import IClothingRepository


class UpdateItem:
    def __init__(self, repo: IClothingRepository):
        self._repo = repo

    async def execute(
            self,
            *,
            item_id: uuid.UUID,
            embedding: list[float],
            user_id: uuid.UUID,
    ) -> None:
        item = await self._repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )
        if item.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        await self._repo.update_embedding(
            item_id=item_id, embedding=embedding
        )
