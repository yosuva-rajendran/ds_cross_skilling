from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.endpoint import EndpointResponse
from app.services.ingestion_service import IngestionService
from app.services.git_service import GitService
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


@router.post(
    "/{project_id}/ingest-source",
    response_model=IngestionResponse,
)
async def ingest_source_code(
    project_id: int,
    version: str = Form(default="1.0.0"),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Ingest a Python/FastAPI source file to extract endpoints and Pydantic models.

    Upload a .py file containing FastAPI route decorators and Pydantic models.
    Provide a version string (defaults to "1.0.0").
    """
    service = IngestionService(session)

    try:
        content = await file.read()
        source_code = content.decode("utf-8")

        return service.ingest_source_code(
            project_id=project_id,
            version=version,
            source_code=source_code,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.post(
    "/{project_id}/ingest-git",
)
async def ingest_from_git(
    project_id: int,
    file_path: str = Query(default="openapi.json", description="Path to spec file in the repo"),
    branch: str = Query(default="main", description="Git branch to walk"),
    max_commits: int = Query(default=10, description="Max commits to process"),
    session: Session = Depends(get_session),
):
    """Ingest API specs from Git commit history.

    Clones the project's repository_url, walks commits that changed the target file,
    and ingests each version. Supports both OpenAPI specs (.json/.yaml) and
    Python source files (.py).

    The project must have a repository_url configured.
    """
    try:
        service = GitService(session)
        results = service.ingest_from_git(
            project_id=project_id,
            file_path=file_path,
            branch=branch,
            max_commits=max_commits,
        )
        return {
            "commits_processed": len(results),
            "versions": results,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git operation failed: {str(e)}",
        )