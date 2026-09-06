from sqlmodel import Session, select

from app.models.component_schema import ComponentSchema


class ComponentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_many(
        self,
        components: list[ComponentSchema],
    ) -> list[ComponentSchema]:
        self.session.add_all(components)
        self.session.commit()

        for component in components:
            self.session.refresh(component)

        return components

    def get_by_project(
        self,
        project_id: int,
    ) -> list[ComponentSchema]:
        statement = select(ComponentSchema).where(
            ComponentSchema.project_id == project_id
        )
        return list(self.session.exec(statement).all())

    def get_by_version(
        self,
        version_id: int,
    ) -> list[ComponentSchema]:
        statement = select(ComponentSchema).where(
            ComponentSchema.version_id == version_id
        )
        return list(self.session.exec(statement).all())