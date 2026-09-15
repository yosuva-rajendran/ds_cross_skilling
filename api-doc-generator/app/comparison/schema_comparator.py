from typing import Any

from app.comparison.change_types import BREAKING, NON_BREAKING

CONSTRAINT_FIELDS = (
    "format", "enum",
    "minimum", "maximum",
    "minLength", "maxLength",
    "pattern", "minItems", "maxItems",
)


def compare_schema_constraints(
    old_schema: dict[str, Any] | None,
    new_schema: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    old = old_schema or {}
    new = new_schema or {}

    for field in CONSTRAINT_FIELDS:
        old_val = old.get(field)
        new_val = new.get(field)

        if old_val != new_val:
            severity = BREAKING
            if field == "format" and old_val is None:
                severity = NON_BREAKING

            changes.append({
                "field": field,
                "old_value": old_val,
                "new_value": new_val,
                "severity": severity,
                "message": f"Constraint '{field}' changed from '{old_val}' to '{new_val}'.",
            })

    return changes


def compare_object_properties(
    old_schema: dict[str, Any] | None,
    new_schema: dict[str, Any] | None,
    context: str = "request",
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []

    old_props = (old_schema or {}).get("properties", {}) or {}
    new_props = (new_schema or {}).get("properties", {}) or {}
    old_required = set((old_schema or {}).get("required", []) or [])
    new_required = set((new_schema or {}).get("required", []) or [])

    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())

    for prop in sorted(new_keys - old_keys):
        is_required = prop in new_required
        if context == "request" and is_required:
            changes.append({
                "kind": "added",
                "field": prop,
                "old_value": None,
                "new_value": _prop_summary(new_props[prop]),
                "severity": BREAKING,
                "message": f"Required property '{prop}' was added.",
            })
        else:
            label = "Response property" if context == "response" else "Optional property"
            changes.append({
                "kind": "added",
                "field": prop,
                "old_value": None,
                "new_value": _prop_summary(new_props[prop]),
                "severity": NON_BREAKING,
                "message": f"{label} '{prop}' was added.",
            })

    for prop in sorted(old_keys - new_keys):
        changes.append({
            "kind": "removed",
            "field": prop,
            "old_value": _prop_summary(old_props[prop]),
            "new_value": None,
            "severity": BREAKING,
            "message": f"Property '{prop}' was removed.",
        })

    for prop in sorted(old_keys & new_keys):
        old_type = old_props[prop].get("type") if isinstance(old_props[prop], dict) else None
        new_type = new_props[prop].get("type") if isinstance(new_props[prop], dict) else None

        if old_type != new_type:
            changes.append({
                "kind": "type_changed",
                "field": prop,
                "old_value": old_type,
                "new_value": new_type,
                "severity": BREAKING,
                "message": f"Property '{prop}' type changed from '{old_type}' to '{new_type}'.",
            })

    if context == "request":
        for prop in sorted(old_keys & new_keys):
            was_required = prop in old_required
            is_required = prop in new_required

            if not was_required and is_required:
                changes.append({
                    "kind": "required_changed",
                    "field": prop,
                    "old_value": "optional",
                    "new_value": "required",
                    "severity": BREAKING,
                    "message": f"Property '{prop}' changed from optional to required.",
                })
            elif was_required and not is_required:
                changes.append({
                    "kind": "required_changed",
                    "field": prop,
                    "old_value": "required",
                    "new_value": "optional",
                    "severity": NON_BREAKING,
                    "message": f"Property '{prop}' changed from required to optional.",
                })

    return changes


def _prop_summary(prop: Any) -> str | None:
    if isinstance(prop, dict):
        return prop.get("type", "unknown")
    return str(prop) if prop is not None else None
