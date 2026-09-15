from sqlmodel import Session

from app.comparison.endpoint_comparator import compare_endpoints
from app.comparison.component_comparator import compare_components
from app.schemas.comparison import Change, ComparisonSummary
from app.services.version_snapshot_service import VersionSnapshotService


class VersionComparisonService:

    def __init__(self, session: Session):
        self.snapshot_service = VersionSnapshotService(session)

    def compare_versions(
        self,
        project_id: int,
        from_version_id: int,
        to_version_id: int,
    ) -> dict:
        if from_version_id == to_version_id:
            raise ValueError("Cannot compare a version with itself.")

        from_snapshot = self.snapshot_service.get_snapshot(project_id, from_version_id)
        to_snapshot = self.snapshot_service.get_snapshot(project_id, to_version_id)

        endpoint_changes = compare_endpoints(
            from_snapshot["endpoints"],
            to_snapshot["endpoints"],
        )

        component_changes = compare_components(
            from_snapshot["components"],
            to_snapshot["components"],
        )

        all_changes: list[Change] = endpoint_changes + component_changes

        summary = ComparisonSummary(
            breaking=sum(1 for c in all_changes if c.severity == "breaking"),
            non_breaking=sum(1 for c in all_changes if c.severity == "non_breaking"),
            informational=sum(1 for c in all_changes if c.severity == "informational"),
        )

        return {
            "from_version": from_snapshot["version"],
            "to_version": to_snapshot["version"],
            "summary": summary,
            "changes": all_changes,
        }
