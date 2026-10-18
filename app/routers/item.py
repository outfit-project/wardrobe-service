import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Response, UploadFile

from app.core.config import settings
from app.core.security.deps import get_current_user
from app.repositories.storage.image_proxy import image_proxy
from app.schemas.categories import Category, Style
from app.schemas.item_upload import (
    UpdateEmbeddingRequest,
    UpdateProcessingRequest,
    UploadClothingItemResponse,
    WardrobeResponse,
)
from app.schemas.user import UserPayload
from app.use_cases.item_case import (
    DeleteClothingItemDep,
    GetClothingItemImageDep,
    GetUserWardrobeDep,
    UploadClothingItemDep,
    UpdateClothingItemDep,
)

item_router = APIRouter()


@item_router.get("/", response_model=WardrobeResponse)
async def list_user_items(
    use_case: GetUserWardrobeDep,
    user: UserPayload = Depends(get_current_user),
) -> WardrobeResponse:
    items = await use_case.execute(user_id=user.user_id)
    return WardrobeResponse(
        items=[
            it.model_copy(update={"image_url": image_proxy(it.id)})
            for it in items
        ],
        total=len(items),
    )


@item_router.post("/upload", response_model=UploadClothingItemResponse)
async def upload_item(
    use_case: UploadClothingItemDep,
    user: UserPayload = Depends(get_current_user),
    category: str | None = Form(None),
    image: UploadFile = File(...),
    subcategory: str | None = Form(None),
    style: str | None = Form(None),
    color_hex: str | None = Form(None),
) -> UploadClothingItemResponse:
    try:
        cat = Category(category) if category else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid category") from e

    st: Style | None = None
    if style:
        try:
            st = Style(style)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid style") from e

    result = await use_case.execute(
        user_id=user.user_id,
        category=cat,
        file_obj=image.file,
        content_type=image.content_type,
        filename=image.filename,
        subcategory=subcategory,
        style=st,
        color_hex=color_hex,
    )
    item_id = UUID(result["item_id"])
    return UploadClothingItemResponse(
        item_id=result["item_id"],
        image_url=image_proxy(item_id),
        processing_status=result["processing_status"],
    )


@item_router.get("/{item_id}/image")
async def get_item_image(
    item_id: UUID,
    use_case: GetClothingItemImageDep,
) -> Response:
    try:
        data, content_type = await use_case.execute_public(item_id=item_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@item_router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: UUID,
    use_case: DeleteClothingItemDep,
    user: UserPayload = Depends(get_current_user),
) -> Response:
    deleted = await use_case.execute(item_id=item_id, user_id=user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return Response(status_code=204)


@item_router.patch("/embedding")
async def update_item_embedding(
    body: UpdateEmbeddingRequest,
    use_case: UpdateClothingItemDep,
    x_service_token: str = Header(default=""),
) -> Response:
    if not settings.ML_SERVICE_TOKEN or not hmac.compare_digest(
        x_service_token, settings.ML_SERVICE_TOKEN
    ):
        raise HTTPException(status_code=401, detail="Invalid service token")
    if len(body.embedding) != settings.EMBEDDING_DIM:
        raise HTTPException(status_code=422, detail="Invalid embedding dimension")
    await use_case.execute(
        item_id=body.item_id,
        embedding=body.embedding,
        category=body.category,
        style=body.style
    )

    return Response(status_code=200)


@item_router.patch("/processing")
async def update_item_processing(
    body: UpdateProcessingRequest,
    use_case: UpdateClothingItemDep,
    x_service_token: str = Header(default=""),
) -> Response:
    if not settings.ML_SERVICE_TOKEN or not hmac.compare_digest(x_service_token, settings.ML_SERVICE_TOKEN):
        raise HTTPException(401, "Invalid service token")
    if body.embedding is not None and len(body.embedding) != settings.EMBEDDING_DIM:
        raise HTTPException(422, "Invalid embedding dimension")
    await use_case.processing(body)
    return Response(status_code=200)


@item_router.post("/{item_id}/retry", response_model=UploadClothingItemResponse)
async def retry_item(
    item_id: UUID,
    use_case: UploadClothingItemDep,
    user: UserPayload = Depends(get_current_user),
) -> UploadClothingItemResponse:
    result = await use_case.retry(item_id=item_id,user_id=user.user_id)
    return UploadClothingItemResponse(**result,image_url=image_proxy(item_id))
