import uuid
from typing import Optional

from sqlalchemy import select, update
from fastapi import Response
from app.models import ItemORM
from app.schemas.item_upload import ClothingItem


class IClothingRepository:
    def __init__(self, session):
        self._session = session

    async def save(self, item: ClothingItem):
        self._session.add(item)

        await self._session.commit()
        await self._session.refresh(item)

        return Response(status_code=201)

    async def get_by_id(self, item_id: uuid.UUID) -> Optional[ClothingItem]:
        query = select(ItemORM).where(ItemORM.id == item_id)
        item = await self._session.execute(query)

        result = item.scalars().one_or_none()

        return result

    async def list_by_user(self, user_id: uuid.UUID) -> list[ClothingItem]:
        query = select(ItemORM).where(ItemORM.user_id == user_id)

        items = await self._session.execute(query)
        result = items.scalars().all()

        return result

    async def update_embedding(self, item_id: uuid.UUID, embedding: list[float]):
        stmt = update(ItemORM).where(ItemORM.id == item_id).values(embedding=embedding)

        await self._session.execute(stmt)
        await self._session.commit()
