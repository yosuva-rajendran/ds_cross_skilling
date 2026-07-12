from fastapi import APIRouter, Depends, HTTPException
from app.qdrant import get_qdrant_client
from qdrant_client import QdrantClient
from app.schemas.collection import CreateCollectionRequest, CollectionResponse, CollectionListResponse
from app.services.collection_service import CollectionService
from app.repositories.collection_repository import CollectionRepository

router = APIRouter(prefix="/collections", tags=["Collections"])


def get_collection_service(
    client: QdrantClient = Depends(get_qdrant_client),
) -> CollectionService:
    repo = CollectionRepository(client)
    return CollectionService(repo)


@router.post("/", response_model=CollectionResponse, status_code=201)
def create_collection(
    req: CreateCollectionRequest,
    service: CollectionService = Depends(get_collection_service),
):
    created = service.create_collection(req.name, req.vector_size, recreate=req.recreate)
    if not created:
        raise HTTPException(status_code=409, detail="Collection already exists")
    return CollectionResponse(name=req.name, status="created")


@router.get("/", response_model=CollectionListResponse)
def list_collections(
    service: CollectionService = Depends(get_collection_service),
):
    return CollectionListResponse(collections=service.list_collections())


@router.delete("/{name}", response_model=CollectionResponse)
def delete_collection(
    name: str,
    service: CollectionService = Depends(get_collection_service),
):
    deleted = service.delete_collection(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Collection not found")
    return CollectionResponse(name=name, status="deleted")