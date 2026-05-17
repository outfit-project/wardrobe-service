from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile

from app.core.security.deps import get_current_user
from app.repositories.storage.image_proxy import image_proxy
from app.schemas.categories import Category, Style
from app.schemas.item_upload import (
    UpdateEmbeddingRequest,
    UploadClothingItemResponse,
    WardrobeResponse,
)
from app.schemas.user import UserPayload
from app.use_cases.item_case import (
    GetClothingItemImageDep,
    GetUserWardrobeDep,
    UploadClothingItemDep, UpdateClothingItemDep,
)

item_router = APIRouter()


@item_router.get("/", response_model=WardrobeResponse)
async def list_user_items(
    request: Request,
    use_case: GetUserWardrobeDep,
    user: UserPayload = Depends(get_current_user),
) -> WardrobeResponse:
    items = await use_case.execute(user_id=user.user_id)
    return WardrobeResponse(
        items=[
            it.model_copy(update={"image_url": image_proxy(request, it.id)})
            for it in items
        ],
        total=len(items),
    )


@item_router.post("/upload", response_model=UploadClothingItemResponse)
async def upload_item(
    request: Request,
    use_case: UploadClothingItemDep,
    user: UserPayload = Depends(get_current_user),
    category: str = Form(...),
    image: UploadFile = File(...),
    subcategory: str | None = Form(None),
    style: str | None = Form(None),
    color_hex: str | None = Form(None),
) -> UploadClothingItemResponse:
    try:
        cat = Category(category)
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
        image_url=image_proxy(request, item_id),
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


@item_router.patch("/embedding")
async def update_item_embedding(
    body: UpdateEmbeddingRequest,
    use_case: UpdateClothingItemDep,
) -> Response:
    await use_case.execute(
        item_id=body.item_id,
        embedding=body.embedding,
    )
    return Response(status_code=200)