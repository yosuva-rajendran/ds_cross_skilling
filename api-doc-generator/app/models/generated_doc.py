from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class GeneratedDoc(SQLModel, table=True):
    __tablename__ = "generated_docs"

    id: int | None = Field(default=None, primary_key=True)

    endpoint_id: int = Field(foreign_key="endpoints.id")

    version_id: int = Field(foreign_key="api_versions.id")

    description: str | None = None

    usage_example: str | None = None

    error_codes: dict[str, str] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )
