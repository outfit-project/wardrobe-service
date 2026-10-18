import io
import uuid
from uuid import UUID
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from app.schemas.categories import Category, Style
from app.schemas.item_upload import ClothingItem, ItemUploadedEvent

MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_FORMATS = {'JPEG': ('jpg','image/jpeg'), 'PNG': ('png','image/png'), 'WEBP': ('webp','image/webp')}


def validated_image(file_obj, content_type):
    if content_type not in {value[1] for value in IMAGE_FORMATS.values()}:
        raise HTTPException(415, 'Use a JPEG, PNG or WebP image')
    data = file_obj.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, 'Image must be at most 10 MB')
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in IMAGE_FORMATS:
                raise HTTPException(415, 'Use a JPEG, PNG or WebP image')
            if image.width * image.height > 10_000_000:
                raise HTTPException(413, 'Image must be at most 10 million pixels')
            ext, actual_type = IMAGE_FORMATS[image.format]
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(400, 'Image could not be decoded') from exc
    return io.BytesIO(data), ext, actual_type


class UploadItem:
    def __init__(self, repo, storage, events):
        self._repo, self._storage, self._events = repo, storage, events

    async def _enqueue(self, item):
        try:
            await self._events.publish(ItemUploadedEvent(item_id=item.id,user_id=item.user_id,image_url=item.image_url))
            status = 'pending'
        except Exception:
            status = 'failed'
            await self._repo.update_processing(item.id,processing_status=status,processing_error='Could not queue photo processing. Please retry.')
        return {'item_id':str(item.id),'processing_status':status}

    async def execute(self, *, user_id: UUID, file_obj, filename: str | None,
                      content_type: str | None, category: Category | None = None,
                      subcategory: str | None = None, style: Style | None = None,
                      color_hex: str | None = None):
        image, ext, mime = validated_image(file_obj, content_type)
        item_id = uuid.uuid4()
        key = f'users/{user_id}/items/{item_id}.{ext}'
        await self._storage.upload_image(image,key,content_type=mime)
        item = ClothingItem(id=item_id,user_id=user_id,image_url=key,category=category,
                            subcategory=subcategory,style=style,color_hex=color_hex)
        await self._repo.save(item)
        return await self._enqueue(item)

    async def retry(self, *, item_id: UUID, user_id: UUID):
        item = await self._repo.get_by_id(item_id)
        if not item or item.user_id != user_id:
            raise HTTPException(404,'Item not found')
        if not await self._repo.claim_retry(item_id,user_id):
            raise HTTPException(409,'Only failed items can be retried')
        return await self._enqueue(item)
