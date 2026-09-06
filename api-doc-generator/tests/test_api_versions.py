"""Tests for version snapshot and comparison API endpoints."""

import pytest
from sqlmodel import Session

from app.models.project import Project
from app.models.api_version import APIVersion
from app.models.endpoint import Endpoint
from app.models.component_schema import ComponentSchema


def _create_project(session: Session, name: str = "Test") -> Project:
    project = Project(name=name)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def _create_version(session: Session, project_id: int, version: str) -> APIVersion:
    v = APIVersion(project_id=project_id, version=version)
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


def _create_endpoint(session: Session, project_id: int, version_id: int, **kwargs) -> Endpoint:
    ep = Endpoint(
        project_id=project_id,
        version_id=version_id,
        path=kwargs.get("path", "/test"),
        method=kwargs.get("method", "GET"),
        summary=kwargs.get("summary"),
        description=kwargs.get("description"),
        parameters=kwargs.get("parameters"),
        request_body=kwargs.get("request_body"),
        responses=kwargs.get("responses"),
        security=kwargs.get("security"),
        tags=kwargs.get("tags"),
        operation_id=kwargs.get("operation_id"),
    )
    session.add(ep)
    session.commit()
    session.refresh(ep)
    return ep


def _create_component(session: Session, project_id: int, version_id: int, **kwargs) -> ComponentSchema:
    comp = ComponentSchema(
        project_id=project_id,
        version_id=version_id,
        name=kwargs.get("name", "TestSchema"),
        description=kwargs.get("description"),
        schema_type=kwargs.get("schema_type", "object"),
        properties=kwargs.get("properties"),
        required=kwargs.get("required"),
    )
    session.add(comp)
    session.commit()
    session.refresh(comp)
    return comp


# ── Version Snapshot Tests ──


class TestVersionSnapshot:
    def test_get_snapshot(self, client, session):
        project = _create_project(session)
        version = _create_version(session, project.id, "1.0.0")
        _create_endpoint(session, project.id, version.id, path="/users", method="GET")
        _create_component(session, project.id, version.id, name="User", properties={"id": {"type": "integer"}})

        response = client.get(f"/projects/{project.id}/versions/{version.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["version"]["version"] == "1.0.0"
        assert len(data["endpoints"]) == 1
        assert len(data["components"]) == 1

    def test_version_not_found(self, client, session):
        project = _create_project(session)

        response = client.get(f"/projects/{project.id}/versions/999")

        assert response.status_code == 404

    def test_version_belongs_to_different_project(self, client, session):
        project1 = _create_project(session, "Project 1")
        project2 = _create_project(session, "Project 2")
        version = _create_version(session, project2.id, "1.0.0")

        response = client.get(f"/projects/{project1.id}/versions/{version.id}")

        assert response.status_code == 404


# ── Version Comparison Tests ──


class TestVersionComparison:
    def test_same_version_comparison(self, client, session):
        project = _create_project(session)
        version = _create_version(session, project.id, "1.0.0")

        response = client.get(f"/projects/{project.id}/versions/{version.id}/compare/{version.id}")

        assert response.status_code == 400

    def test_compare_version_not_found(self, client, session):
        project = _create_project(session)
        version = _create_version(session, project.id, "1.0.0")

        response = client.get(f"/projects/{project.id}/versions/{version.id}/compare/999")

        assert response.status_code == 404

    def test_compare_version_different_project(self, client, session):
        project1 = _create_project(session, "Project 1")
        project2 = _create_project(session, "Project 2")
        v1 = _create_version(session, project1.id, "1.0.0")
        v2 = _create_version(session, project2.id, "1.0.0")

        response = client.get(f"/projects/{project1.id}/versions/{v1.id}/compare/{v2.id}")

        assert response.status_code == 404

    def test_compare_endpoint_added(self, client, session):
        project = _create_project(session)
        v1 = _create_version(session, project.id, "1.0.0")
        v2 = _create_version(session, project.id, "1.1.0")

        _create_endpoint(session, project.id, v1.id, path="/users", method="GET")
        _create_endpoint(session, project.id, v2.id, path="/users", method="GET")
        _create_endpoint(session, project.id, v2.id, path="/users", method="POST")

        response = client.get(f"/projects/{project.id}/versions/{v1.id}/compare/{v2.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["non_breaking"] >= 1

        added = [c for c in data["changes"] if c["type"] == "endpoint_added"]
        assert len(added) == 1
        assert added[0]["method"] == "POST"

    def test_compare_endpoint_removed(self, client, session):
        project = _create_project(session)
        v1 = _create_version(session, project.id, "1.0.0")
        v2 = _create_version(session, project.id, "1.1.0")

        _create_endpoint(session, project.id, v1.id, path="/users", method="GET")
        _create_endpoint(session, project.id, v1.id, path="/users/{id}", method="DELETE")
        _create_endpoint(session, project.id, v2.id, path="/users", method="GET")

        response = client.get(f"/projects/{project.id}/versions/{v1.id}/compare/{v2.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["breaking"] >= 1

        removed = [c for c in data["changes"] if c["type"] == "endpoint_removed"]
        assert len(removed) == 1

    def test_compare_required_parameter_added(self, client, session):
        project = _create_project(session)
        v1 = _create_version(session, project.id, "1.0.0")
        v2 = _create_version(session, project.id, "1.1.0")

        _create_endpoint(
            session, project.id, v1.id,
            path="/users/{username}", method="GET",
            parameters=[{"name": "username", "required": True}],
        )
        _create_endpoint(
            session, project.id, v2.id,
            path="/users/{username}", method="GET",
            parameters=[
                {"name": "username", "required": True},
                {"name": "tenant_id", "required": True},
            ],
        )

        response = client.get(f"/projects/{project.id}/versions/{v1.id}/compare/{v2.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["breaking"] >= 1

        breaking = [c for c in data["changes"] if c["type"] == "required_parameter_added"]
        assert len(breaking) == 1
        assert breaking[0]["field"] == "tenant_id"

    def test_compare_response_structure(self, client, session):
        """Verify the response has the expected top-level structure."""
        project = _create_project(session)
        v1 = _create_version(session, project.id, "1.0.0")
        v2 = _create_version(session, project.id, "1.1.0")

        response = client.get(f"/projects/{project.id}/versions/{v1.id}/compare/{v2.id}")

        assert response.status_code == 200
        data = response.json()

        assert "from_version" in data
        assert "to_version" in data
        assert "summary" in data
        assert "changes" in data
        assert data["from_version"]["version"] == "1.0.0"
        assert data["to_version"]["version"] == "1.1.0"
        assert "breaking" in data["summary"]
        assert "non_breaking" in data["summary"]
        assert "informational" in data["summary"]

    def test_compare_component_changes(self, client, session):
        project = _create_project(session)
        v1 = _create_version(session, project.id, "1.0.0")
        v2 = _create_version(session, project.id, "1.1.0")

        _create_component(session, project.id, v1.id, name="User", properties={"id": {"type": "integer"}})
        _create_component(session, project.id, v2.id, name="User", properties={
            "id": {"type": "integer"},
            "email": {"type": "string"},
        })

        response = client.get(f"/projects/{project.id}/versions/{v1.id}/compare/{v2.id}")

        assert response.status_code == 200
        data = response.json()

        prop_added = [c for c in data["changes"] if c["type"] == "component_property_added"]
        assert len(prop_added) == 1
        assert prop_added[0]["component"] == "User"
        assert prop_added[0]["field"] == "email"


# ── Ingestion Duplicate Version Test ──


class TestIngestionDuplicateVersion:
    def test_duplicate_version_returns_409(self, client, session):
        project = _create_project(session)
        _create_version(session, project.id, "1.0.0")

        openapi_spec = b"""{
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }"""

        import io
        response = client.post(
            f"/projects/{project.id}/ingest",
            files={"file": ("spec.json", io.BytesIO(openapi_spec), "application/json")},
        )

        assert response.status_code == 409
