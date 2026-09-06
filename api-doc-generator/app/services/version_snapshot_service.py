from sqlmodel import Session

from app.repositories.api_version_repository import APIVersionRepository
from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.component_repository import ComponentRepository


class VersionSnapshotService:
    """Retrieves a complete snapshot of an API version including its endpoints and components."""

    def __init__(self, session: Session):
        self.version_repository = APIVersionRepository(session)
        self.endpoint_repository = EndpointRepository(session)
        self.component_repository = ComponentRepository(session)

    def get_snapshot(self, project_id: int, version_id: int) -> dict:
        """Get a complete version snapshot with endpoints and components.

        Validates that the version exists and belongs to the specified project.

        Raises:
            ValueError: If the version is not found or belongs to a different project.
        """
        version = self.version_repository.get_by_id(version_id)

        if not version:
            raise ValueError(f"Version with id {version_id} not found")

        if version.project_id != project_id:
            raise ValueError(f"Version {version_id} does not belong to project {project_id}")

        endpoints = self.endpoint_repository.get_by_version(version_id)
        components = self.component_repository.get_by_version(version_id)

        return {
            "version": version,
            "endpoints": endpoints,
            "components": components,
        }
