from sqlmodel import Session

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:

    def __init__(self, session: Session):
        self.repository = ProjectRepository(session)

    def create_project(self, data: ProjectCreate) -> Project:
        project = Project(
            name=data.name,
            repository_url=data.repository_url,
        )

        return self.repository.create(project)

    def get_projects(self) -> list[Project]:
        return self.repository.get_all()

    def get_project(self, project_id: int) -> Project | None:
        return self.repository.get_by_id(project_id)

    def delete_project(self, project_id: int) -> bool:
        project = self.repository.get_by_id(project_id)

        if not project:
            return False

        self.repository.delete(project)

        return True