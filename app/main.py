import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.redis import close_redis
from app.db.session import engine
from app.routers import health as health_router
from app.routers.item import item_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(settings.SERVICE_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    await engine.dispose()
    await close_redis()


app = FastAPI(
    title=settings.SERVICE_NAME,
    lifespan=lifespan,
)

app.include_router(health_router.router, prefix="/health", tags=["health"])
app.include_router(item_router, prefix="/items", tags=["item"])

@app.get("/")
async def root() -> dict:
    return {"service": settings.SERVICE_NAME, "status": "ok"}
