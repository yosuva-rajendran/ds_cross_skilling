from typing import Any

from pydantic import BaseModel

from app.schemas.api_version import APIVersionResponse
from app.schemas.endpoint import EndpointResponse


class ComponentResponse(BaseModel):
    id: int
    project_id: int
    version_id: int
    name: str
    description: str | None = None
    schema_type: str | None = None
    properties: dict[str, Any] | None = None
    required: list[str] | None = None


class IngestionResponse(BaseModel):
    version: APIVersionResponse
    endpoints: list[EndpointResponse]
    components: list[ComponentResponse]