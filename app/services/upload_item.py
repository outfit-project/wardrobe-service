import os
import uuid
from  uuid import UUID

from fastapi import Depends, Form

from app.core.security.deps import get_current_user
from app.interfaces.event_abc import IEventPublisher
from app.interfaces.image_abc import IImageStorage
from app.interfaces.item_abc import IClothingRepository
from app.schemas.categories import Category, Style
from app.schemas.item_upload import ClothingItem, ItemUploadedEvent


class UploadItem:
    def __init__(
            self,
            repo: IClothingRepository,
            storage: IImageStorage,
            events: IEventPublisher
    ):
        self._repo = repo
        self._storage = storage
        self._events = events

    async def execute(
            self,
            *,
            user_id: UUID,
            file_obj,
            filename: str | None,
            category: Category,
            content_type: str | None,
            subcategory: str | None = None,
            style: Style | None = None,
            color_hex: str | None = None,
    ):
        item_id = uuid.uuid4()
        raw_name = filename or ""

        ext = os.path.splitext(raw_name)[1].lstrip(".").lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        key = f"users/{user_id}/items/{item_id}.{ext}"

        await self._storage.upload_image(file_obj, key, content_type=content_type)

        st = style or Style.UNDEFINED

        item = ClothingItem(
            id=item_id,
            user_id=user_id,
            category=category,
            image_url=key,
            subcategory=subcategory,
            style=st,
            color_hex=color_hex,
            embedding=None
        )
        await self._repo.save(item)
        await self._events.publish(
            ItemUploadedEvent(item_id=item_id, user_id=user_id, image_url=key)
        )

        return {"item_id": str(item_id)}