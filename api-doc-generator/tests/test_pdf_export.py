"""Tests for PDF export."""

import pytest
from sqlmodel import Session

from app.models.project import Project
from app.models.api_version import APIVersion
from app.models.endpoint import Endpoint
from app.models.generated_doc import GeneratedDoc
from app.models.component_schema import ComponentSchema
from app.services.pdf_service import PDFService


def _setup_data(session: Session):
    """Create test data for PDF generation."""
    project = Project(name="Test API")
    session.add(project)
    session.commit()
    session.refresh(project)

    version = APIVersion(project_id=project.id, version="1.0.0")
    session.add(version)
    session.commit()
    session.refresh(version)

    ep = Endpoint(
        project_id=project.id, version_id=version.id,
        path="/users/{id}", method="GET",
        summary="Get a user",
        parameters=[{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        responses={"200": {"description": "OK"}, "404": {"description": "Not found"}},
    )
    session.add(ep)
    session.commit()
    session.refresh(ep)

    doc = GeneratedDoc(
        endpoint_id=ep.id, version_id=version.id,
        description="Retrieves a user by their unique ID.",
        usage_example='curl -X GET "https://api.example.com/users/42"',
        error_codes={"200": "Success", "404": "User not found"},
    )
    session.add(doc)

    comp = ComponentSchema(
        project_id=project.id, version_id=version.id,
        name="User", schema_type="object",
        properties={"id": {"type": "integer"}, "name": {"type": "string"}},
        required=["id", "name"],
    )
    session.add(comp)
    session.commit()

    return project, version


class TestPDFGeneration:
    def test_generates_valid_pdf(self, session):
        project, version = _setup_data(session)

        service = PDFService(session)
        pdf_bytes = service.generate_pdf(project.id, version.id)

        # PDF files start with %PDF
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 100

    def test_version_not_found(self, session):
        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        service = PDFService(session)
        with pytest.raises(ValueError):
            service.generate_pdf(project.id, 999)

    def test_pdf_without_generated_docs(self, session):
        """PDF should work even without LLM-generated docs."""
        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        version = APIVersion(project_id=project.id, version="1.0.0")
        session.add(version)
        session.commit()
        session.refresh(version)

        ep = Endpoint(
            project_id=project.id, version_id=version.id,
            path="/health", method="GET", summary="Health check",
        )
        session.add(ep)
        session.commit()

        service = PDFService(session)
        pdf_bytes = service.generate_pdf(project.id, version.id)
        assert pdf_bytes[:5] == b"%PDF-"


class TestPDFRoute:
    def test_export_pdf_endpoint(self, client, session):
        project, version = _setup_data(session)

        response = client.get(
            f"/projects/{project.id}/versions/{version.id}/docs/pdf"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content[:5] == b"%PDF-"

    def test_export_pdf_not_found(self, client, session):
        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        response = client.get(f"/projects/{project.id}/versions/999/docs/pdf")
        assert response.status_code == 404
