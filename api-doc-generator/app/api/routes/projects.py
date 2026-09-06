from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project: ProjectCreate,
    session: Session = Depends(get_session),
):
    service = ProjectService(session)

    return service.create_project(project)


@router.get(
    "/",
    response_model=list[ProjectResponse],
)
async def get_projects(
    session: Session = Depends(get_session),
):
    service = ProjectService(session)

    return service.get_projects()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: int,
    session: Session = Depends(get_session),
):
    service = ProjectService(session)

    project = service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
):
    service = ProjectService(session)

    deleted = service.delete_project(project_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )