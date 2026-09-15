from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.project import Project
from app.models.api_version import APIVersion
from app.services.git_service import GitService
from app.services.doc_generation_service import DocGenerationService
from app.services.version_comparison_service import VersionComparisonService
from app.repositories.api_version_repository import APIVersionRepository


router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"],
)


@router.post("/github")
async def github_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    """Receive GitHub push events and auto-ingest API specs.

    Setup in GitHub:
        Repo → Settings → Webhooks → Add webhook
        URL: https://your-server.com/webhook/github
        Content type: application/json
        Events: Just the push event

    The system will:
    1. Find the project by repository_url
    2. Read the spec/source file from the latest commit
    3. Ingest it as a new version
    4. Auto-generate LLM docs
    5. Auto-compare with the previous version and report breaking changes
    """
    payload = await request.json()

    # Only process push events
    ref = payload.get("ref", "")
    if not ref.startswith("refs/heads/"):
        return {"status": "skipped", "reason": "Not a branch push"}

    branch = ref.replace("refs/heads/", "")
    repo_url = payload.get("repository", {}).get("clone_url")

    if not repo_url:
        return {"status": "skipped", "reason": "No repository URL in payload"}

    # Find which project this repo belongs to
    statement = select(Project).where(Project.repository_url == repo_url)
    project = session.exec(statement).first()

    # Also try html_url match
    if not project:
        html_url = payload.get("repository", {}).get("html_url")
        if html_url:
            statement = select(Project).where(Project.repository_url == html_url)
            project = session.exec(statement).first()

    if not project:
        return {"status": "skipped", "reason": f"No project found for repo {repo_url}"}

    # Check which files changed in this push
    changed_files = set()
    for commit in payload.get("commits", []):
        changed_files.update(commit.get("added", []))
        changed_files.update(commit.get("modified", []))

    # Look for spec files in changes
    spec_files = [
        f for f in changed_files
        if f.endswith((".json", ".yaml", ".yml", ".py"))
        and any(keyword in f.lower() for keyword in ("openapi", "swagger", "spec", "routes", "api"))
    ]

    if not spec_files:
        return {
            "status": "skipped",
            "reason": "No API spec or source files changed in this push",
        }

    # Get existing versions BEFORE ingestion (for auto-compare later)
    version_repo = APIVersionRepository(session)
    existing_versions = version_repo.get_by_project(project.id)
    previous_version = existing_versions[-1] if existing_versions else None

    # Ingest from git for each changed spec file
    results = []
    git_service = GitService(session)

    for file_path in spec_files:
        try:
            ingestion_results = git_service.ingest_from_git(
                project_id=project.id,
                file_path=file_path,
                branch=branch,
                max_commits=1,
            )

            for result in ingestion_results:
                # Auto-generate docs
                try:
                    statement = select(APIVersion).where(
                        APIVersion.project_id == project.id,
                        APIVersion.version == result["version"],
                    )
                    new_version = session.exec(statement).first()

                    if new_version:
                        doc_service = DocGenerationService(session)
                        doc_service.generate_for_version(new_version.id)
                        result["docs_generated"] = True

                        # Auto-compare with previous version
                        if previous_version and previous_version.id != new_version.id:
                            try:
                                comp_service = VersionComparisonService(session)
                                comparison = comp_service.compare_versions(
                                    project.id, previous_version.id, new_version.id,
                                )
                                result["comparison"] = {
                                    "from_version": previous_version.version,
                                    "to_version": new_version.version,
                                    "breaking": comparison["summary"].breaking,
                                    "non_breaking": comparison["summary"].non_breaking,
                                    "informational": comparison["summary"].informational,
                                    "changes": [
                                        {
                                            "type": c.type,
                                            "severity": c.severity,
                                            "message": c.message,
                                        }
                                        for c in comparison["changes"]
                                    ],
                                }
                            except Exception:
                                result["comparison"] = None
                except Exception:
                    result["docs_generated"] = False

            results.extend(ingestion_results)

        except (ValueError, RuntimeError) as e:
            results.append({
                "file": file_path,
                "error": str(e),
            })

    return {
        "status": "processed",
        "project": project.name,
        "branch": branch,
        "files_processed": len(spec_files),
        "results": results,
    }
