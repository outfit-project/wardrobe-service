import uuid

from app.interfaces.item_abc import IClothingRepository


class DeleteItem:
    def __init__(self, repo: IClothingRepository):
        self._repo = repo

    async def execute(self, *, item_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return await self._repo.delete(item_id=item_id, user_id=user_id)
