from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.projects import router as project_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.include_router(project_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok"
    }