from typing import Protocol, runtime_checkable


@runtime_checkable
class IImageStorage(Protocol):
    async def upload_image(self, file_obj, key: str, *, content_type: str | None = None):
        pass

    async def get_bytes(self, key: str) -> tuple[bytes, str]:
        pass
