"""Service that orchestrates version comparison using snapshot data and comparators."""

from sqlmodel import Session

from app.comparison.endpoint_comparator import compare_endpoints
from app.comparison.component_comparator import compare_components
from app.schemas.comparison import Change, ComparisonSummary
from app.services.version_snapshot_service import VersionSnapshotService


class VersionComparisonService:
    """Compares two API version snapshots and produces a structured change report."""

    def __init__(self, session: Session):
        self.snapshot_service = VersionSnapshotService(session)

    def compare_versions(
        self,
        project_id: int,
        from_version_id: int,
        to_version_id: int,
    ) -> dict:
        """Compare two versions and return structured change results.

        Args:
            project_id: The project both versions must belong to.
            from_version_id: The baseline version ID.
            to_version_id: The target version ID.

        Raises:
            ValueError: If versions are the same, not found, or belong to different projects.
        """
        if from_version_id == to_version_id:
            raise ValueError("Cannot compare a version with itself.")

        from_snapshot = self.snapshot_service.get_snapshot(project_id, from_version_id)
        to_snapshot = self.snapshot_service.get_snapshot(project_id, to_version_id)

        # Compare endpoints
        endpoint_changes = compare_endpoints(
            from_snapshot["endpoints"],
            to_snapshot["endpoints"],
        )

        # Compare components
        component_changes = compare_components(
            from_snapshot["components"],
            to_snapshot["components"],
        )

        all_changes: list[Change] = endpoint_changes + component_changes

        # Build summary
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
