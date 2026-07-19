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

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[dict]:
        response = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
        )
        return [
            {
                "text": hit.payload["text"],
                "score": hit.score,
                "filename": hit.payload["filename"],
                "chunk_index": hit.payload["chunk_index"],
                "document_id": hit.payload["document_id"],
            }
            for hit in response.points
        ]
