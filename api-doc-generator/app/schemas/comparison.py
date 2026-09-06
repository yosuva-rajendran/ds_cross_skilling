from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.api_version import APIVersionResponse


class Change(BaseModel):
    """A single detected change between two API versions."""

    type: str
    severity: Literal["breaking", "non_breaking", "informational"]
    method: str | None = None
    path: str | None = None
    component: str | None = None
    field: str | None = None
    old_value: Any | None = None
    new_value: Any | None = None
    message: str


class ComparisonSummary(BaseModel):
    breaking: int = 0
    non_breaking: int = 0
    informational: int = 0


class ComparisonResponse(BaseModel):
    from_version: APIVersionResponse
    to_version: APIVersionResponse
    summary: ComparisonSummary
    changes: list[Change]
