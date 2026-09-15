from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.projects import router as project_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.versions import router as version_router
from app.api.routes.docs import router as docs_router
from app.api.routes.webhook import router as webhook_router
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
app.include_router(ingestion_router)
app.include_router(version_router)
app.include_router(docs_router)
app.include_router(webhook_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}