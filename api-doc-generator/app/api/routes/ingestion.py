from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.endpoint import EndpointResponse
from app.services.ingestion_service import IngestionService
from app.schemas.ingestion import IngestionResponse


router = APIRouter(
    prefix="/projects",
    tags=["Ingestion"],
)


@router.post(
    "/{project_id}/ingest",
    response_model=IngestionResponse,
)
async def ingest_openapi(
    project_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    service = IngestionService(session)

    try:
        content = await file.read()

        return service.ingest_openapi(
            project_id=project_id,
            filename=file.filename or "",
            content=content,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )