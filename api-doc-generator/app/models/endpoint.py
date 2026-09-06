from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class Endpoint(SQLModel, table=True):
    __tablename__ = "endpoints"

    id: int | None = Field(default=None, primary_key=True)

    project_id: int = Field(foreign_key="projects.id")

    path: str
    method: str

    tags: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )

    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None

    parameters: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )

    request_body: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )

    responses: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )

    security: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSON),
    )