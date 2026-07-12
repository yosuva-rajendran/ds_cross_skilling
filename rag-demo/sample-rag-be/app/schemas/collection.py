from pydantic import BaseModel


class CreateCollectionRequest(BaseModel):
    name: str
    vector_size: int
    recreate: bool = False


class CollectionResponse(BaseModel):
    name: str
    status: str


class CollectionListResponse(BaseModel):
    collections: list[str]