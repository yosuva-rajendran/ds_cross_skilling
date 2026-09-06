from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    repository_url: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    repository_url: str | None = None