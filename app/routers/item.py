from fastapi import APIRouter

from app.services import UploadItem

item_router = APIRouter(prefix="/items")


@item_router.get("/", response_model=UploadItem)
async def