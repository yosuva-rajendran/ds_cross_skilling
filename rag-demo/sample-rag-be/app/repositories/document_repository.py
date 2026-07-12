from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app.qdrant import get_qdrant_client


class DocumentRepository:

    def __init__(self):
        self.client: QdrantClient = get_qdrant_client()

    def store(
        self,
        collection_name: str,
        document_id: str,
        filename: str,
        chunks: list[str],
        vectors: list[list[float]],
    ):

        points = []

        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):

            points.append(
                PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": index,
                        "text": chunk,
                    },
                )
            )

        self.client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )