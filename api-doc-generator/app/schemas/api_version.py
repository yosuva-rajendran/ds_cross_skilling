from pydantic import BaseModel, Field


class APIVersionCreate(BaseModel):
    version: str = Field(
        min_length=1,
        max_length=50,
    )


class APIVersionResponse(BaseModel):
    id: int
    project_id: int
    version: str