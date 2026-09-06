from typing import Any

from pydantic import BaseModel

from app.schemas.api_version import APIVersionResponse
from app.schemas.endpoint import EndpointResponse
from app.schemas.ingestion import ComponentResponse


class VersionSnapshotResponse(BaseModel):
    version: APIVersionResponse
    endpoints: list[EndpointResponse]
    components: list[ComponentResponse]
