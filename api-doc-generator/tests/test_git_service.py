"""Tests for Git commit history ingestion service."""

import pytest
from unittest.mock import patch, MagicMock
from sqlmodel import Session

from app.models.project import Project
from app.services.git_service import GitService


def _create_project(session: Session, repo_url: str | None = None) -> Project:
    project = Project(name="Test", repository_url=repo_url)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


class TestGitServiceValidation:
    def test_project_not_found(self, session):
        service = GitService(session)
        with pytest.raises(ValueError, match="not found"):
            service.ingest_from_git(project_id=999)

    def test_no_repository_url(self, session):
        project = _create_project(session, repo_url=None)

        service = GitService(session)
        with pytest.raises(ValueError, match="no repository_url"):
            service.ingest_from_git(project_id=project.id)

    def test_local_repo_path_not_exists(self, session):
        project = _create_project(session)

        service = GitService(session)
        with pytest.raises(ValueError, match="does not exist"):
            service.ingest_from_local_repo(
                project_id=project.id,
                repo_path="/nonexistent/path",
            )


class TestGitCommitParsing:
    def test_get_commits_for_file(self, session):
        project = _create_project(session, repo_url="https://github.com/test/repo")

        service = GitService(session)

        # Mock _run_git to return commit log output
        with patch.object(service, "_run_git") as mock_git:
            mock_git.return_value = (
                "abc1234|2024-01-15|Initial API spec\n"
                "def5678|2024-02-20|Updated endpoints\n"
                "ghi9012|2024-03-10|Added users endpoint\n"
            )

            commits = service._get_commits_for_file("/tmp/repo", "openapi.json", 10)

        assert len(commits) == 3
        assert commits[0] == ("abc1234", "2024-01-15", "Initial API spec")
        assert commits[1] == ("def5678", "2024-02-20", "Updated endpoints")
        assert commits[2] == ("ghi9012", "2024-03-10", "Added users endpoint")

    def test_empty_commit_log(self, session):
        project = _create_project(session, repo_url="https://github.com/test/repo")

        service = GitService(session)

        with patch.object(service, "_run_git") as mock_git:
            mock_git.return_value = ""

            commits = service._get_commits_for_file("/tmp/repo", "openapi.json", 10)

        assert len(commits) == 0


class TestGitIngestionFlow:
    @patch.object(GitService, "_run_git")
    def test_ingest_from_local_repo(self, mock_git, session):
        import os
        project = _create_project(session)

        service = GitService(session)

        spec_content = '{"openapi":"3.0.0","info":{"title":"Test","version":"1.0.0"},"paths":{"/health":{"get":{"summary":"Health check","responses":{"200":{"description":"OK"}}}}}}'

        # Mock commit log
        mock_git.side_effect = [
            # First call: git log
            "abc1234|2024-01-15|Initial spec\n",
            # Second call: git show
            spec_content,
        ]

        with patch("os.path.isdir", return_value=True):
            results = service.ingest_from_local_repo(
                project_id=project.id,
                repo_path="/tmp/fake-repo",
                file_path="openapi.json",
            )

        assert len(results) == 1
        assert results[0]["commit"] == "abc1234"
        assert results[0]["version"] == "2024-01-15-abc1234"
        assert results[0]["endpoints_count"] == 1
