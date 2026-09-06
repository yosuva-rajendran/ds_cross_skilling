from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.version_snapshot import VersionSnapshotResponse
from app.schemas.comparison import ComparisonResponse
from app.services.version_snapshot_service import VersionSnapshotService
from app.services.version_comparison_service import VersionComparisonService


router = APIRouter(
    prefix="/projects",
    tags=["Versions"],
)


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
