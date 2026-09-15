from typing import Any

from app.comparison.change_types import (
    BREAKING,
    NON_BREAKING,
    COMPONENT_ADDED,
    COMPONENT_REMOVED,
    COMPONENT_PROPERTY_ADDED,
    COMPONENT_PROPERTY_REMOVED,
    COMPONENT_PROPERTY_TYPE_CHANGED,
    COMPONENT_REQUIRED_CHANGED,
)
from app.comparison.schema_comparator import compare_object_properties
from app.schemas.comparison import Change

_KIND_TO_TYPE = {
    "added": COMPONENT_PROPERTY_ADDED,
    "removed": COMPONENT_PROPERTY_REMOVED,
    "type_changed": COMPONENT_PROPERTY_TYPE_CHANGED,
    "required_changed": COMPONENT_REQUIRED_CHANGED,
}


def compare_components(
    old_components: list[Any],
    new_components: list[Any],
) -> list[Change]:
    changes: list[Change] = []

    old_map = {c.name: c for c in old_components}
    new_map = {c.name: c for c in new_components}

    old_names = set(old_map.keys())
    new_names = set(new_map.keys())

    for name in sorted(new_names - old_names):
        changes.append(Change(
            type=COMPONENT_ADDED, severity=NON_BREAKING,
            component=name,
            message=f"Component '{name}' was added.",
        ))

    for name in sorted(old_names - new_names):
        changes.append(Change(
            type=COMPONENT_REMOVED, severity=BREAKING,
            component=name,
            message=f"Component '{name}' was removed.",
        ))

    for name in sorted(old_names & new_names):
        old_comp = old_map[name]
        new_comp = new_map[name]

        old_schema = _component_to_schema_dict(old_comp)
        new_schema = _component_to_schema_dict(new_comp)

        for pc in compare_object_properties(old_schema, new_schema, context="request"):
            change_type = _KIND_TO_TYPE.get(pc["kind"], COMPONENT_PROPERTY_ADDED)
            changes.append(Change(
                type=change_type, severity=pc["severity"],
                component=name, field=pc["field"],
                old_value=pc["old_value"], new_value=pc["new_value"],
                message=f"{pc['message'].rstrip('.')} in component '{name}'.",
            ))

    return changes


def _component_to_schema_dict(comp: Any) -> dict[str, Any]:
    return {
        "properties": comp.properties or {},
        "required": comp.required or [],
    }
