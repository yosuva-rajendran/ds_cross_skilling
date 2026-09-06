"""Compares OpenAPI schema objects and detects breaking/non-breaking changes."""

from typing import Any

from app.comparison.change_types import (
    BREAKING,
    NON_BREAKING,
    INFORMATIONAL,
)

# Schema constraint fields that affect compatibility
CONSTRAINT_FIELDS = (
    "type", "format", "enum",
    "minimum", "maximum",
    "minLength", "maxLength",
    "pattern", "minItems", "maxItems",
)


def compare_schema_type(
    old_schema: dict[str, Any] | None,
    new_schema: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Compare the top-level type of two schemas.

    Returns a list of change dicts with keys: field, old_value, new_value, severity, message.
    """
    changes: list[dict[str, Any]] = []

    old_type = (old_schema or {}).get("type")
    new_type = (new_schema or {}).get("type")

    if old_type != new_type:
        changes.append({
            "field": "type",
            "old_value": old_type,
            "new_value": new_type,
            "severity": BREAKING,
            "message": f"Schema type changed from '{old_type}' to '{new_type}'.",
        })

    return changes


def compare_schema_constraints(
    old_schema: dict[str, Any] | None,
    new_schema: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Compare constraint fields between two schemas.

    Returns changes for type, format, enum, min/max, pattern, etc.
    """
    changes: list[dict[str, Any]] = []
    old = old_schema or {}
    new = new_schema or {}

    for field in CONSTRAINT_FIELDS:
        old_val = old.get(field)
        new_val = new.get(field)

        if old_val != new_val:
            severity = BREAKING
            if field in ("format",) and old_val is None:
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
    """Compare properties of two object schemas.

    Args:
        old_schema: The old schema dict.
        new_schema: The new schema dict.
        context: Either "request" or "response" - affects severity classification.

    Returns:
        List of change dicts.
    """
    changes: list[dict[str, Any]] = []

    old_props = (old_schema or {}).get("properties", {}) or {}
    new_props = (new_schema or {}).get("properties", {}) or {}
    old_required = set((old_schema or {}).get("required", []) or [])
    new_required = set((new_schema or {}).get("required", []) or [])

    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())

    # Added properties
    for prop in sorted(new_keys - old_keys):
        if context == "request":
            if prop in new_required:
                changes.append({
                    "field": prop,
                    "old_value": None,
                    "new_value": _prop_summary(new_props[prop]),
                    "severity": BREAKING,
                    "message": f"Required property '{prop}' was added.",
                })
            else:
                changes.append({
                    "field": prop,
                    "old_value": None,
                    "new_value": _prop_summary(new_props[prop]),
                    "severity": NON_BREAKING,
                    "message": f"Optional property '{prop}' was added.",
                })
        else:
            changes.append({
                "field": prop,
                "old_value": None,
                "new_value": _prop_summary(new_props[prop]),
                "severity": NON_BREAKING,
                "message": f"Response property '{prop}' was added.",
            })

    # Removed properties
    for prop in sorted(old_keys - new_keys):
        changes.append({
            "field": prop,
            "old_value": _prop_summary(old_props[prop]),
            "new_value": None,
            "severity": BREAKING,
            "message": f"Property '{prop}' was removed.",
        })

    # Modified properties
    for prop in sorted(old_keys & new_keys):
        old_prop = old_props[prop]
        new_prop = new_props[prop]

        old_type = old_prop.get("type") if isinstance(old_prop, dict) else None
        new_type = new_prop.get("type") if isinstance(new_prop, dict) else None

        if old_type != new_type:
            changes.append({
                "field": prop,
                "old_value": old_type,
                "new_value": new_type,
                "severity": BREAKING,
                "message": f"Property '{prop}' type changed from '{old_type}' to '{new_type}'.",
            })

    # Required field changes (for existing properties)
    for prop in sorted(old_keys & new_keys):
        was_required = prop in old_required
        is_required = prop in new_required

        if not was_required and is_required and context == "request":
            changes.append({
                "field": prop,
                "old_value": "optional",
                "new_value": "required",
                "severity": BREAKING,
                "message": f"Property '{prop}' changed from optional to required.",
            })
        elif was_required and not is_required and context == "request":
            changes.append({
                "field": prop,
                "old_value": "required",
                "new_value": "optional",
                "severity": NON_BREAKING,
                "message": f"Property '{prop}' changed from required to optional.",
            })

    return changes


def _prop_summary(prop: Any) -> str | None:
    """Create a short summary of a property for change reporting."""
    if isinstance(prop, dict):
        return prop.get("type", "unknown")
    return str(prop) if prop is not None else None
