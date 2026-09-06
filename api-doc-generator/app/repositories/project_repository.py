from sqlmodel import Session, select

from app.models.project import Project


class ProjectRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, project: Project) -> Project:
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)

        return project

    def get_all(self) -> list[Project]:
        statement = select(Project)

        return list(
            self.session.exec(statement).all()
        )

    def get_by_id(self, project_id: int) -> Project | None:
        return self.session.get(Project, project_id)

    def delete(self, project: Project) -> None:
        self.session.delete(project)
        self.session.commit()