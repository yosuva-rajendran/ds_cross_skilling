import os
import subprocess
import tempfile

from sqlmodel import Session

from app.services.ingestion_service import IngestionService
from app.repositories.project_repository import ProjectRepository


class GitService:

    def __init__(self, session: Session):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.ingestion_service = IngestionService(session)

    def ingest_from_git(
        self,
        project_id: int,
        file_path: str = "openapi.json",
        branch: str = "main",
        max_commits: int = 10,
    ) -> list[dict]:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if not project.repository_url:
            raise ValueError(f"Project {project_id} has no repository_url configured")

        results = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            self._run_git(["git", "clone", "--branch", branch, project.repository_url, tmp_dir])
            commits = self._get_commits_for_file(tmp_dir, file_path, max_commits)

            for commit_sha, commit_date, commit_msg in commits:
                try:
                    file_content = self._get_file_at_commit(tmp_dir, commit_sha, file_path)

                    if file_content is None:
                        continue

                    short_sha = commit_sha[:7]
                    version = f"{commit_date}-{short_sha}"

                    if file_path.endswith(".py"):
                        result = self.ingestion_service.ingest_source_code(
                            project_id=project_id,
                            version=version,
                            source_code=file_content,
                        )
                    else:
                        result = self.ingestion_service.ingest_openapi(
                            project_id=project_id,
                            filename=file_path,
                            content=file_content.encode("utf-8"),
                        )

                    results.append({
                        "commit": commit_sha,
                        "date": commit_date,
                        "message": commit_msg,
                        "version": version,
                        "endpoints_count": len(result["endpoints"]),
                        "components_count": len(result["components"]),
                    })

                except ValueError:
                    # Skip commits that produce duplicate versions
                    continue

        return results

    def ingest_from_local_repo(
        self,
        project_id: int,
        repo_path: str,
        file_path: str = "openapi.json",
        branch: str = "main",
        max_commits: int = 10,
    ) -> list[dict]:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path {repo_path} does not exist")

        results = []
        commits = self._get_commits_for_file(repo_path, file_path, max_commits)

        for commit_sha, commit_date, commit_msg in commits:
            try:
                file_content = self._get_file_at_commit(repo_path, commit_sha, file_path)

                if file_content is None:
                    continue

                short_sha = commit_sha[:7]
                version = f"{commit_date}-{short_sha}"

                if file_path.endswith(".py"):
                    result = self.ingestion_service.ingest_source_code(
                        project_id=project_id,
                        version=version,
                        source_code=file_content,
                    )
                else:
                    result = self.ingestion_service.ingest_openapi(
                        project_id=project_id,
                        filename=file_path,
                        content=file_content.encode("utf-8"),
                    )

                results.append({
                    "commit": commit_sha,
                    "date": commit_date,
                    "message": commit_msg,
                    "version": version,
                    "endpoints_count": len(result["endpoints"]),
                    "components_count": len(result["components"]),
                })

            except ValueError:
                continue

        return results

    def _get_commits_for_file(
        self,
        repo_path: str,
        file_path: str,
        max_commits: int,
    ) -> list[tuple[str, str, str]]:
        output = self._run_git([
            "git", "-C", repo_path, "log",
            "--reverse",
            f"-{max_commits}",
            "--format=%H|%as|%s",
            "--", file_path,
        ])

        commits = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))

        return commits

    def _get_file_at_commit(
        self,
        repo_path: str,
        commit_sha: str,
        file_path: str,
    ) -> str | None:
        try:
            return self._run_git([
                "git", "-C", repo_path, "show",
                f"{commit_sha}:{file_path}",
            ])
        except RuntimeError:
            return None

    def _run_git(self, cmd: list[str]) -> str:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr.strip()}")

        return result.stdout
