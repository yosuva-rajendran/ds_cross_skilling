from typing import Any

from pydantic import BaseModel


class EndpointResponse(BaseModel):
    id: int
    project_id: int
    path: str
    method: str

    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    operation_id: str | None = None

    parameters: list[dict[str, Any]] | None = None
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] | None = None
    security: list[dict[str, Any]] | None = None