from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class APIVersion(SQLModel, table=True):
    __tablename__ = "api_versions"

    id: int | None = Field(default=None, primary_key=True)

    project_id: int = Field(
        foreign_key="projects.id"
    )

    version: str

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "version",
            name="uq_project_version",
        ),
    )