from qdrant_client.models import Distance
from app.repositories.collection_repository import CollectionRepository
import logging

logger = logging.getLogger(__name__)


class CollectionService:
    def __init__(self, repo: CollectionRepository):
        self.repo = repo

    def create_collection(
        self, name: str, vector_size: int,
        distance: Distance = Distance.COSINE, recreate: bool = False,
    ) -> bool:
        if self.repo.exists(name):
            if not recreate:
                logger.info(f"'{name}' already exists")
                return False
            self.repo.delete(name)

        self.repo.create(name, vector_size, distance)
        logger.info(f"Created '{name}' (size={vector_size})")
        return True

    def delete_collection(self, name: str) -> bool:
        if not self.repo.exists(name):
            return False
        self.repo.delete(name)
        return True

    def list_collections(self) -> list[str]:
        return self.repo.list_all()