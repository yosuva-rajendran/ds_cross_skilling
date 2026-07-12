from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CollectionInfo


class CollectionRepository:
    def __init__(self, client: QdrantClient):
        self.client = client

    def exists(self, name: str) -> bool:
        return self.client.collection_exists(name)

    def create(self, name: str, vector_size: int, distance: Distance) -> None:
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )

    def delete(self, name: str) -> None:
        self.client.delete_collection(name)

    def get_info(self, name: str) -> CollectionInfo:
        return self.client.get_collection(name)

    def list_all(self) -> list[str]:
        return [c.name for c in self.client.get_collections().collections]