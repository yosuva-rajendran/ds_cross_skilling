from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.services.indexing_service import IndexingService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

indexing_service = IndexingService()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_document(
    collection_name: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a PDF and index it into the specified collection.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required."
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    try:
        result = await indexing_service.index_document(
            collection_name=collection_name,
            file=file
        )
        return {
            "message": "Document indexed successfully.",
            "data": result
        }
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex))