"""Compares components/schemas between two API versions and detects changes."""

from typing import Any

from app.comparison.change_types import (
    BREAKING,
    NON_BREAKING,
    INFORMATIONAL,
    COMPONENT_ADDED,
    COMPONENT_REMOVED,
    COMPONENT_PROPERTY_ADDED,
    COMPONENT_PROPERTY_REMOVED,
    COMPONENT_PROPERTY_TYPE_CHANGED,
    COMPONENT_REQUIRED_CHANGED,
)
from app.schemas.comparison import Change


def compare_components(
    old_components: list[Any],
    new_components: list[Any],
) -> list[Change]:
    """Compare two sets of components and return all detected changes.

    Components are matched by name.
    """
    changes: list[Change] = []

    old_map: dict[str, Any] = {c.name: c for c in old_components}
    new_map: dict[str, Any] = {c.name: c for c in new_components}

    old_names = set(old_map.keys())
    new_names = set(new_map.keys())

    # Added components
    for name in sorted(new_names - old_names):
        changes.append(Change(
            type=COMPONENT_ADDED,
            severity=NON_BREAKING,
            component=name,
            message=f"Component '{name}' was added.",
        ))

    # Removed components
    for name in sorted(old_names - new_names):
        changes.append(Change(
            type=COMPONENT_REMOVED,
            severity=BREAKING,
            component=name,
            message=f"Component '{name}' was removed.",
        ))

    # Modified components
    for name in sorted(old_names & new_names):
        old_comp = old_map[name]
        new_comp = new_map[name]

        changes.extend(_compare_component_properties(name, old_comp, new_comp))
        changes.extend(_compare_component_required(name, old_comp, new_comp))

    return changes


def _compare_component_properties(
    name: str,
    old_comp: Any,
    new_comp: Any,
) -> list[Change]:
    """Compare properties of two component schemas."""
    changes: list[Change] = []

    old_props = old_comp.properties or {}
    new_props = new_comp.properties or {}

    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())

    # Added properties
    for prop in sorted(new_keys - old_keys):
        new_required = set(new_comp.required or [])
        if prop in new_required:
            changes.append(Change(
                type=COMPONENT_PROPERTY_ADDED,
                severity=BREAKING,
                component=name,
                field=prop,
                new_value=_prop_type(new_props[prop]),
                message=f"Required property '{prop}' was added to component '{name}'.",
            ))
        else:
            changes.append(Change(
                type=COMPONENT_PROPERTY_ADDED,
                severity=NON_BREAKING,
                component=name,
                field=prop,
                new_value=_prop_type(new_props[prop]),
                message=f"Optional property '{prop}' was added to component '{name}'.",
            ))

    # Removed properties
    for prop in sorted(old_keys - new_keys):
        changes.append(Change(
            type=COMPONENT_PROPERTY_REMOVED,
            severity=BREAKING,
            component=name,
            field=prop,
            old_value=_prop_type(old_props[prop]),
            message=f"Property '{prop}' was removed from component '{name}'.",
        ))

    # Modified properties (type changes)
    for prop in sorted(old_keys & new_keys):
        old_type = _prop_type(old_props[prop])
        new_type = _prop_type(new_props[prop])

        if old_type != new_type:
            changes.append(Change(
                type=COMPONENT_PROPERTY_TYPE_CHANGED,
                severity=BREAKING,
                component=name,
                field=prop,
                old_value=old_type,
                new_value=new_type,
                message=f"Property '{prop}' type changed from '{old_type}' to '{new_type}' in component '{name}'.",
            ))

    return changes


def _compare_component_required(
    name: str,
    old_comp: Any,
    new_comp: Any,
) -> list[Change]:
    """Compare required field lists between two components."""
    changes: list[Change] = []

    old_required = set(old_comp.required or [])
    new_required = set(new_comp.required or [])

    old_props = set((old_comp.properties or {}).keys())
    new_props = set((new_comp.properties or {}).keys())

    # Only check fields that exist in both versions
    common_props = old_props & new_props

    for prop in sorted(common_props):
        was_required = prop in old_required
        is_required = prop in new_required

        if not was_required and is_required:
            changes.append(Change(
                type=COMPONENT_REQUIRED_CHANGED,
                severity=BREAKING,
                component=name,
                field=prop,
                old_value="optional",
                new_value="required",
                message=f"Property '{prop}' changed from optional to required in component '{name}'.",
            ))
        elif was_required and not is_required:
            changes.append(Change(
                type=COMPONENT_REQUIRED_CHANGED,
                severity=NON_BREAKING,
                component=name,
                field=prop,
                old_value="required",
                new_value="optional",
                message=f"Property '{prop}' changed from required to optional in component '{name}'.",
            ))

    return changes


def _prop_type(prop: Any) -> str | None:
    """Extract the type from a property definition."""
    if isinstance(prop, dict):
        return prop.get("type")
    return None
