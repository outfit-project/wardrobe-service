from typing import Protocol, runtime_checkable

from app.schemas.item_upload import ItemUploadedEvent

@runtime_checkable
class IEventPublisher(Protocol):
    async def publish(self, event: ItemUploadedEvent) -> None:
        pass

