from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class ComponentSchema(SQLModel, table=True):
    __tablename__ = "component_schemas"

    id: int | None = Field(default=None, primary_key=True)

    project_id: int = Field(
        foreign_key="projects.id"
    )

    version_id: int = Field(
        foreign_key="api_versions.id"
    )

    name: str
    description: str | None = None
    schema_type: str | None = None

    properties: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )

    required: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )