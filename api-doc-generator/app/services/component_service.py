from sqlmodel import Session

from app.models.component_schema import ComponentSchema
from app.repositories.component_repository import ComponentRepository


class ComponentService:
    def __init__(self, session: Session):
        self.repository = ComponentRepository(session)

    def save_components(
        self,
        project_id: int,
        version_id: int,
        parsed_components: list[dict],
    ) -> list[ComponentSchema]:

        components = [
            ComponentSchema(
                project_id=project_id,
                version_id=version_id,
                name=data["name"],
                description=data["description"],
                schema_type=data["schema_type"],
                properties=data["properties"],
                required=data["required"],
            )
            for data in parsed_components
        ]

        return self.repository.create_many(components)