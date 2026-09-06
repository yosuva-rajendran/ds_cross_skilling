from sqlmodel import Session, select

from app.models.endpoint import Endpoint


class EndpointRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, endpoint: Endpoint) -> Endpoint:
        self.session.add(endpoint)
        self.session.commit()
        self.session.refresh(endpoint)

        return endpoint

    def create_many(
        self,
        endpoints: list[Endpoint],
    ) -> list[Endpoint]:
        self.session.add_all(endpoints)
        self.session.commit()

        for endpoint in endpoints:
            self.session.refresh(endpoint)

        return endpoints

    def get_by_project(
        self,
        project_id: int,
    ) -> list[Endpoint]:
        statement = select(Endpoint).where(
            Endpoint.project_id == project_id
        )

        return list(self.session.exec(statement).all())

    def get_by_version(self, version_id: int) -> list[Endpoint]:
        statement = select(Endpoint).where(
            Endpoint.version_id == version_id
        )
        return list(self.session.exec(statement).all())