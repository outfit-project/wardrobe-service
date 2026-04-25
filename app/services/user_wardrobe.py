import uuid

from app.interfaces.item_abc import IClothingRepository
from app.schemas.item_upload import ClothingItem


class GetUserWardrobe:
    def __init__(
            self,
            repo: IClothingRepository
    ):
        self._repo = repo

    async def execute(self, user_id: uuid.UUID) -> list[ClothingItem]:
        return await self._repo.list_by_user(user_id)



