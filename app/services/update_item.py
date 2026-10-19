import uuid
from fastapi import HTTPException

from app.interfaces.item_abc import IClothingRepository


class UpdateItem:
    def __init__(self, repo: IClothingRepository): self._repo = repo

    async def execute(self, *, item_id: uuid.UUID, embedding: list[float], style=None, category=None):
        if not await self._repo.get_by_id(item_id):
            raise HTTPException(404, 'Item not found')
        values = {'embedding':embedding}
        if category is not None: values['category'] = category
        if style is not None: values['style'] = style
        await self._repo.update_processing(item_id, **values)

    async def processing(self, body):
        if not await self._repo.get_by_id(body.item_id):
            raise HTTPException(404,'Item not found')
        values = body.model_dump(exclude_unset=True,exclude={'item_id'})
        if body.processing_status == 'ready': values['processing_error'] = None
        if body.processing_status == 'processing': values['processing_error'] = None
        await self._repo.update_processing(body.item_id, **values)
