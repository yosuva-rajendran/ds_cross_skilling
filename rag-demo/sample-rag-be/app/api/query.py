from fastapi import APIRouter, HTTPException, status

from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/query", tags=["Query"])

retrieval_service = RetrievalService()


@router.post("/", response_model=QueryResponse)
async def query_documents(req: QueryRequest):
    try:
        return retrieval_service.query(
            collection_name=req.collection_name,
            query=req.query,
            top_k=req.top_k,
            generate_answer=req.generate_answer,
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ex),
        )
