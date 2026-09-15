from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.version_snapshot import VersionSnapshotResponse
from app.schemas.api_version import APIVersionResponse
from app.schemas.comparison import ComparisonResponse
from app.services.version_snapshot_service import VersionSnapshotService
from app.services.version_comparison_service import VersionComparisonService
from app.services.change_explanation_service import ChangeExplanationService
from app.repositories.api_version_repository import APIVersionRepository


router = APIRouter(
    prefix="/projects",
    tags=["Versions"],
)


@router.get(
    "/{project_id}/versions",
    response_model=list[APIVersionResponse],
)
async def list_versions(
    project_id: int,
    session: Session = Depends(get_session),
):
    """List all API versions for a project."""
    repo = APIVersionRepository(session)
    return repo.get_by_project(project_id)


@router.get(
    "/{project_id}/versions/{version_id}",
    response_model=VersionSnapshotResponse,
)
async def get_version_snapshot(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_session),
):
    service = VersionSnapshotService(session)

    try:
        return service.get_snapshot(project_id, version_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{project_id}/versions/{from_version_id}/compare/{to_version_id}",
    response_model=ComparisonResponse,
)
async def compare_versions(
    project_id: int,
    from_version_id: int,
    to_version_id: int,
    session: Session = Depends(get_session),
):
    service = VersionComparisonService(session)

    try:
        return service.compare_versions(
            project_id=project_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
        )
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower() or "does not belong" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


@router.get(
    "/{project_id}/versions/{from_version_id}/compare/{to_version_id}/explain",
)
async def explain_changes(
    project_id: int,
    from_version_id: int,
    to_version_id: int,
    session: Session = Depends(get_session),
):
    """Compare two versions and generate LLM explanations using function calling / tools.

    The LLM decides which tool to call for each change:
    - explain_breaking_change: impact, migration steps, risk level
    - explain_non_breaking_change: summary, benefits
    """
    try:
        service = ChangeExplanationService(session)
        return service.explain_changes(
            project_id=project_id,
            from_version_id=from_version_id,
            to_version_id=to_version_id,
        )
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower() or "does not belong" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(e)}",
        )
