import uuid

from app.core.config import settings


def image_proxy(item_id: uuid.UUID) -> str:
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/items/{item_id}/image"