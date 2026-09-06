from sqlmodel import Session

from app.models.api_version import APIVersion
from app.repositories.api_version_repository import APIVersionRepository
from app.schemas.api_version import APIVersionCreate


class APIVersionService:
    def __init__(self, session: Session):
        self.repository = APIVersionRepository(session)

    def create_version(
        self,
        project_id: int,
        data: APIVersionCreate,
    ) -> APIVersion:
        api_version = APIVersion(
            project_id=project_id,
            version=data.version,
        )

        return self.repository.create(api_version)

    def get_versions(
        self,
        project_id: int,
    ) -> list[APIVersion]:
        return self.repository.get_by_project(project_id)

    def get_version(
        self,
        version_id: int,
    ) -> APIVersion | None:
        return self.repository.get_by_id(version_id)