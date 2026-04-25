from fastapi import Request
import uuid

def image_proxy(request: Request, item_id:uuid.UUID) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/items/{item_id}/image"