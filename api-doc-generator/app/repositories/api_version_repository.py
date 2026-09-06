from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.api_version import APIVersion


class APIVersionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, api_version: APIVersion) -> APIVersion:
        try:
            self.session.add(api_version)
            self.session.commit()
            self.session.refresh(api_version)
            return api_version

        except IntegrityError:
            self.session.rollback()
            raise ValueError(
                f"Version {api_version.version} already exists "
                f"for project {api_version.project_id}"
            )

    def get_by_project(self, project_id: int) -> list[APIVersion]:
        statement = select(APIVersion).where(
            APIVersion.project_id == project_id
        )
        return list(self.session.exec(statement).all())

    def get_by_id(self, version_id: int) -> APIVersion | None:
        return self.session.get(APIVersion, version_id)