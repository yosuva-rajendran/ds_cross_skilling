"""Tests for GitHub webhook endpoint."""

from unittest.mock import patch
from sqlmodel import Session

from app.models.project import Project


def _create_project(session: Session, repo_url: str) -> Project:
    project = Project(name="Test", repository_url=repo_url)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


class TestGitHubWebhook:
    def test_skips_non_branch_push(self, client, session):
        response = client.post("/webhook/github", json={
            "ref": "refs/tags/v1.0.0",
            "repository": {"clone_url": "https://github.com/test/repo.git"},
        })

        assert response.status_code == 200
        assert response.json()["status"] == "skipped"

    def test_skips_unknown_repo(self, client, session):
        response = client.post("/webhook/github", json={
            "ref": "refs/heads/main",
            "repository": {
                "clone_url": "https://github.com/unknown/repo.git",
                "html_url": "https://github.com/unknown/repo",
            },
            "commits": [],
        })

        assert response.status_code == 200
        assert response.json()["status"] == "skipped"
        assert "No project found" in response.json()["reason"]

    def test_skips_no_spec_files_changed(self, client, session):
        _create_project(session, "https://github.com/test/repo.git")

        response = client.post("/webhook/github", json={
            "ref": "refs/heads/main",
            "repository": {
                "clone_url": "https://github.com/test/repo.git",
            },
            "commits": [
                {"added": ["README.md"], "modified": ["setup.py"]},
            ],
        })

        assert response.status_code == 200
        assert response.json()["status"] == "skipped"
        assert "No API spec" in response.json()["reason"]

    def test_detects_spec_file_changes(self, client, session):
        project = _create_project(session, "https://github.com/test/repo.git")

        with patch("app.api.routes.webhook.GitService") as MockGit:
            mock_instance = MockGit.return_value
            mock_instance.ingest_from_git.return_value = [{
                "commit": "abc123",
                "date": "2024-01-15",
                "message": "Update API",
                "version": "2024-01-15-abc123",
                "endpoints_count": 3,
                "components_count": 2,
            }]

            with patch("app.api.routes.webhook.DocGenerationService"):
                response = client.post("/webhook/github", json={
                    "ref": "refs/heads/main",
                    "repository": {
                        "clone_url": "https://github.com/test/repo.git",
                    },
                    "commits": [
                        {"added": [], "modified": ["openapi.json"]},
                    ],
                })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["project"] == "Test"
        assert data["files_processed"] == 1

    def test_matches_project_by_html_url(self, client, session):
        _create_project(session, "https://github.com/test/repo")

        response = client.post("/webhook/github", json={
            "ref": "refs/heads/main",
            "repository": {
                "clone_url": "https://github.com/test/repo.git",
                "html_url": "https://github.com/test/repo",
            },
            "commits": [
                {"added": ["api/routes.py"], "modified": []},
            ],
        })

        assert response.status_code == 200
        # Should find the project via html_url fallback
        assert response.json()["status"] != "skipped" or "No project" not in response.json().get("reason", "")
