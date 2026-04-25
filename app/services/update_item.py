import uuid

from sqlalchemy import update

from app.interfaces.event_abc import IEventPublisher
from app.interfaces.image_abc import IImageStorage
from app.interfaces.item_abc import IClothingRepository
from app.models import ItemORM


class UpdateItem:
    def __init__(
            self,
            repo: IClothingRepository,
    ):
        self._repo = repo

    async def execute(
            self,
            *,
            item_id:uuid.UUID,
            embedding: list[float]
    ):
      await self._repo.update_embedding(item_id=item_id, embedding=embedding)


