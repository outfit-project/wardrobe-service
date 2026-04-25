import uuid

from pydantic import BaseModel


class ItemUploadedEvent(BaseModel):
    item_id: uuid.UUID
    user_id: uuid.UUID
    image_url: str
