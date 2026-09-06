from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.projects import router as project_router
from app.core.config import settings
from app.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


app.include_router(project_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}