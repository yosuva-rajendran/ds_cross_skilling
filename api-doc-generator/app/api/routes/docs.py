from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.generated_doc import GeneratedDocResponse, DocEvaluationResponse
from app.services.doc_generation_service import DocGenerationService
from app.services.doc_evaluation_service import DocEvaluationService
from app.services.version_snapshot_service import VersionSnapshotService
from app.services.pdf_service import PDFService
from app.repositories.generated_doc_repository import GeneratedDocRepository


router = APIRouter(
    prefix="/projects",
    tags=["Documentation"],
)


@router.post(
    "/{project_id}/versions/{version_id}/generate-docs",
    response_model=list[GeneratedDocResponse],
)
async def generate_docs(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_session),
):
    """Generate LLM-powered documentation for all endpoints in a version.

    Uses GPT-4o with structured output (Pydantic) to generate:
    - Human-readable descriptions
    - Usage examples (curl commands)
    - Error code explanations
    """
    # Validate version belongs to project
    snapshot_service = VersionSnapshotService(session)
    try:
        snapshot_service.get_snapshot(project_id, version_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    try:
        service = DocGenerationService(session)
        return service.generate_for_version(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doc generation failed: {str(e)}",
        )


@router.get(
    "/{project_id}/versions/{version_id}/docs",
    response_model=list[GeneratedDocResponse],
)
async def get_docs(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_session),
):
    """Retrieve previously generated documentation for a version."""
    snapshot_service = VersionSnapshotService(session)
    try:
        snapshot_service.get_snapshot(project_id, version_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    repo = GeneratedDocRepository(session)
    return repo.get_by_version(version_id)


@router.post(
    "/{project_id}/versions/{version_id}/evaluate",
    response_model=list[DocEvaluationResponse],
)
async def evaluate_docs(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_session),
):
    """Evaluate generated documentation using LLM-as-a-Judge.

    Uses GPT-4o to score each generated doc on:
    - accuracy (0.0 - 1.0)
    - completeness (0.0 - 1.0)
    - clarity (0.0 - 1.0)
    """
    snapshot_service = VersionSnapshotService(session)
    try:
        snapshot_service.get_snapshot(project_id, version_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    try:
        service = DocEvaluationService(session)
        return service.evaluate_version(version_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


@router.get(
    "/{project_id}/versions/{version_id}/docs/pdf",
)
async def export_pdf(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_session),
):
    """Export API documentation as a downloadable PDF.

    Includes endpoints, parameters, LLM-generated descriptions,
    usage examples, error codes, and component schemas.
    """
    try:
        service = PDFService(session)
        pdf_bytes = service.generate_pdf(project_id, version_id)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=api-docs-v{version_id}.pdf"
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
