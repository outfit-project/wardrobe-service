import uuid
from typing import Optional

from sqlalchemy import select, update

from app.models import ItemORM
from app.schemas.categories import Category, Style
from app.schemas.item_upload import ClothingItem


def _item_orm_to_schema(row: ItemORM) -> ClothingItem:
    emb = row.embedding
    if emb is None:
        embedding = None
    elif hasattr(emb, "tolist"):
        embedding = [float(x) for x in emb.tolist()]
    else:
        embedding = [float(x) for x in list(emb)]

    return ClothingItem(
        id=row.id,
        user_id=row.user_id,
        category=Category(row.category),
        image_url=row.image_url,
        subcategory=row.subcategory,
        style=Style(row.style) if row.style else Style.UNDEFINED,
        color_hex=row.color_hex,
        embedding=embedding,
        created_at=row.created_at,
    )


def _clothing_item_to_orm(item: ClothingItem) -> ItemORM:
    style_val = item.style.value if item.style is not None else None
    return ItemORM(
        id=item.id,
        user_id=item.user_id,
        category=item.category.value,
        image_url=item.image_url,
        subcategory=item.subcategory,
        style=style_val,
        color_hex=item.color_hex,
        embedding=item.embedding,
    )


class ClothingRepository:
    def __init__(self, session):
        self._session = session

    async def save(self, item: ClothingItem) -> None:
        row = _clothing_item_to_orm(item)
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)

    async def get_by_id(self, item_id: uuid.UUID) -> Optional[ClothingItem]:
        query = select(ItemORM).where(ItemORM.id == item_id)
        result = await self._session.execute(query)
        row = result.scalars().one_or_none()
        if row is None:
            return None
        return _item_orm_to_schema(row)

    async def list_by_user(self, user_id: uuid.UUID) -> list[ClothingItem]:
        query = select(ItemORM).where(ItemORM.user_id == user_id)
        result = await self._session.execute(query)
        rows = result.scalars().all()
        return [_item_orm_to_schema(r) for r in rows]

    async def update_embedding(self, item_id: uuid.UUID, embedding: list[float]) -> None:
        stmt = update(ItemORM).where(ItemORM.id == item_id).values(embedding=embedding)
        await self._session.execute(stmt)
        await self._session.commit()
