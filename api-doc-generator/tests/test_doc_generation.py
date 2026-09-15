"""Tests for LLM-powered doc generation and evaluation with mocked LLM calls."""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session

from app.models.project import Project
from app.models.api_version import APIVersion
from app.models.endpoint import Endpoint
from app.models.generated_doc import GeneratedDoc
from app.services.doc_generation_service import DocGenerationService
from app.services.doc_evaluation_service import DocEvaluationService
from app.schemas.generated_doc import EndpointDocumentation, DocEvaluationOutput


def _create_project(session: Session) -> Project:
    project = Project(name="Test")
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def _create_version(session: Session, project_id: int) -> APIVersion:
    v = APIVersion(project_id=project_id, version="1.0.0")
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


def _create_endpoint(session: Session, project_id: int, version_id: int, **kwargs) -> Endpoint:
    ep = Endpoint(
        project_id=project_id,
        version_id=version_id,
        path=kwargs.get("path", "/users"),
        method=kwargs.get("method", "GET"),
        summary=kwargs.get("summary", "Get users"),
        description=kwargs.get("description"),
        parameters=kwargs.get("parameters", [
            {"name": "limit", "in": "query", "schema": {"type": "integer"}, "required": False}
        ]),
        request_body=kwargs.get("request_body"),
        responses=kwargs.get("responses", {
            "200": {"description": "Success"},
            "400": {"description": "Bad request"},
        }),
        tags=kwargs.get("tags"),
        operation_id=kwargs.get("operation_id"),
        security=kwargs.get("security"),
    )
    session.add(ep)
    session.commit()
    session.refresh(ep)
    return ep


# ── Doc Generation Tests ──


class TestDocGeneration:
    @patch("app.services.doc_generation_service.generate_structured")
    def test_generate_for_version(self, mock_gen, session):
        project = _create_project(session)
        version = _create_version(session, project.id)
        _create_endpoint(session, project.id, version.id)

        mock_gen.return_value = EndpointDocumentation(
            description="Returns a list of users with optional pagination.",
            usage_example='curl -X GET "https://api.example.com/users?limit=10"',
            error_codes={"200": "Success", "400": "Invalid limit parameter"},
        )

        service = DocGenerationService(session)
        docs = service.generate_for_version(version.id)

        assert len(docs) == 1
        assert docs[0].description == "Returns a list of users with optional pagination."
        assert docs[0].usage_example == 'curl -X GET "https://api.example.com/users?limit=10"'
        assert docs[0].error_codes == {"200": "Success", "400": "Invalid limit parameter"}
        assert docs[0].endpoint_id is not None
        assert docs[0].version_id == version.id

        # Verify LLM was called with structured output model
        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs["response_model"] == EndpointDocumentation

    def test_generate_skips_existing_docs(self, session):
        project = _create_project(session)
        version = _create_version(session, project.id)
        endpoint = _create_endpoint(session, project.id, version.id)

        existing_doc = GeneratedDoc(
            endpoint_id=endpoint.id,
            version_id=version.id,
            description="Already exists",
            usage_example="curl ...",
            error_codes={"200": "OK"},
        )
        session.add(existing_doc)
        session.commit()

        service = DocGenerationService(session)
        docs = service.generate_for_version(version.id)

        assert len(docs) == 1
        assert docs[0].description == "Already exists"

    @patch("app.services.doc_generation_service.generate_structured")
    def test_generate_multiple_endpoints(self, mock_gen, session):
        project = _create_project(session)
        version = _create_version(session, project.id)
        _create_endpoint(session, project.id, version.id, path="/users", method="GET")
        _create_endpoint(session, project.id, version.id, path="/users", method="POST",
                         request_body={"content": {"application/json": {"schema": {
                             "type": "object",
                             "properties": {"name": {"type": "string"}},
                         }}}})

        mock_gen.return_value = EndpointDocumentation(
            description="Test description",
            usage_example="curl ...",
            error_codes={"200": "OK"},
        )

        service = DocGenerationService(session)
        docs = service.generate_for_version(version.id)

        assert len(docs) == 2
        assert mock_gen.call_count == 2

    @patch("app.services.doc_generation_service.generate_structured")
    def test_prompt_includes_endpoint_info(self, mock_gen, session):
        project = _create_project(session)
        version = _create_version(session, project.id)
        _create_endpoint(
            session, project.id, version.id,
            path="/orders/{id}", method="DELETE",
            summary="Cancel an order",
        )

        mock_gen.return_value = EndpointDocumentation(
            description="Cancels an order",
            usage_example="curl -X DELETE ...",
            error_codes={"200": "OK"},
        )

        service = DocGenerationService(session)
        service.generate_for_version(version.id)

        call_kwargs = mock_gen.call_args
        user_prompt = call_kwargs.kwargs["user_prompt"]

        assert "DELETE" in user_prompt
        assert "/orders/{id}" in user_prompt
        assert "Cancel an order" in user_prompt


# ── Doc Evaluation Tests ──


class TestDocEvaluation:
    @patch("app.services.doc_evaluation_service.generate_structured")
    def test_evaluate_version(self, mock_gen, session):
        project = _create_project(session)
        version = _create_version(session, project.id)
        endpoint = _create_endpoint(session, project.id, version.id)

        doc = GeneratedDoc(
            endpoint_id=endpoint.id,
            version_id=version.id,
            description="Returns a list of users.",
            usage_example="curl -X GET ...",
            error_codes={"200": "OK", "400": "Bad request"},
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        mock_gen.return_value = DocEvaluationOutput(
            accuracy=0.92,
            completeness=0.85,
            clarity=0.90,
            feedback="Good coverage but missing parameter details.",
        )

        service = DocEvaluationService(session)
        evaluations = service.evaluate_version(version.id)

        assert len(evaluations) == 1
        assert evaluations[0].accuracy == 0.92
        assert evaluations[0].completeness == 0.85
        assert evaluations[0].clarity == 0.90
        assert "missing parameter" in evaluations[0].feedback

        # Verify structured output model was used
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs["response_model"] == DocEvaluationOutput

    def test_evaluate_skips_existing(self, session):
        project = _create_project(session)
        version = _create_version(session, project.id)
        endpoint = _create_endpoint(session, project.id, version.id)

        doc = GeneratedDoc(
            endpoint_id=endpoint.id, version_id=version.id,
            description="Test", usage_example="curl ...", error_codes={},
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        from app.models.doc_evaluation import DocEvaluation
        existing_eval = DocEvaluation(
            generated_doc_id=doc.id,
            accuracy=0.9, completeness=0.8, clarity=0.85,
            feedback="Already evaluated",
        )
        session.add(existing_eval)
        session.commit()

        service = DocEvaluationService(session)
        evaluations = service.evaluate_version(version.id)

        assert len(evaluations) == 1
        assert evaluations[0].feedback == "Already evaluated"


# ── API Route Tests ──


class TestDocRoutes:
    def test_generate_docs_endpoint(self, client, session):
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
            path="/users", method="GET",
            responses={"200": {"description": "OK"}},
        )
        session.add(ep)
        session.commit()

        with patch("app.api.routes.docs.DocGenerationService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.generate_for_version.return_value = [
                GeneratedDoc(
                    id=1, endpoint_id=ep.id, version_id=version.id,
                    description="Lists users",
                    usage_example="curl ...",
                    error_codes={"200": "OK"},
                )
            ]

            response = client.post(
                f"/projects/{project.id}/versions/{version.id}/generate-docs"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Lists users"

    def test_generate_docs_version_not_found(self, client, session):
        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        response = client.post(
            f"/projects/{project.id}/versions/999/generate-docs"
        )

        assert response.status_code == 404

    def test_get_docs_endpoint(self, client, session):
        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        version = APIVersion(project_id=project.id, version="1.0.0")
        session.add(version)
        session.commit()
        session.refresh(version)

        response = client.get(
            f"/projects/{project.id}/versions/{version.id}/docs"
        )

        assert response.status_code == 200
        assert response.json() == []
