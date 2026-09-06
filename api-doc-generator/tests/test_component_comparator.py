"""Tests for component comparison logic."""

import pytest
from types import SimpleNamespace

from app.comparison.component_comparator import compare_components
from app.comparison.change_types import (
    COMPONENT_ADDED,
    COMPONENT_REMOVED,
    COMPONENT_PROPERTY_ADDED,
    COMPONENT_PROPERTY_REMOVED,
    COMPONENT_PROPERTY_TYPE_CHANGED,
    COMPONENT_REQUIRED_CHANGED,
)


def _comp(
    name="User",
    properties=None,
    required=None,
    description=None,
    schema_type="object",
):
    """Create a mock component object."""
    return SimpleNamespace(
        name=name,
        properties=properties,
        required=required,
        description=description,
        schema_type=schema_type,
    )


class TestComponentAddedRemoved:
    def test_component_added(self):
        old = []
        new = [_comp(name="User")]

        changes = compare_components(old, new)

        assert len(changes) == 1
        assert changes[0].type == COMPONENT_ADDED
        assert changes[0].severity == "non_breaking"
        assert changes[0].component == "User"

    def test_component_removed(self):
        old = [_comp(name="User")]
        new = []

        changes = compare_components(old, new)

        assert len(changes) == 1
        assert changes[0].type == COMPONENT_REMOVED
        assert changes[0].severity == "breaking"
        assert changes[0].component == "User"


class TestComponentPropertyChanges:
    def test_property_added_optional(self):
        old = [_comp(
            properties={"id": {"type": "integer"}},
            required=["id"],
        )]
        new = [_comp(
            properties={
                "id": {"type": "integer"},
                "email": {"type": "string"},
            },
            required=["id"],
        )]

        changes = compare_components(old, new)

        added = [c for c in changes if c.type == COMPONENT_PROPERTY_ADDED]
        assert len(added) == 1
        assert added[0].severity == "non_breaking"
        assert added[0].field == "email"

    def test_property_added_required(self):
        old = [_comp(
            properties={"id": {"type": "integer"}},
            required=["id"],
        )]
        new = [_comp(
            properties={
                "id": {"type": "integer"},
                "email": {"type": "string"},
            },
            required=["id", "email"],
        )]

        changes = compare_components(old, new)

        added = [c for c in changes if c.type == COMPONENT_PROPERTY_ADDED]
        assert len(added) == 1
        assert added[0].severity == "breaking"

    def test_property_removed(self):
        old = [_comp(
            properties={
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        )]
        new = [_comp(
            properties={"id": {"type": "integer"}},
        )]

        changes = compare_components(old, new)

        removed = [c for c in changes if c.type == COMPONENT_PROPERTY_REMOVED]
        assert len(removed) == 1
        assert removed[0].severity == "breaking"
        assert removed[0].field == "name"

    def test_property_type_changed(self):
        old = [_comp(
            properties={"age": {"type": "integer"}},
        )]
        new = [_comp(
            properties={"age": {"type": "string"}},
        )]

        changes = compare_components(old, new)

        type_changes = [c for c in changes if c.type == COMPONENT_PROPERTY_TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].severity == "breaking"
        assert type_changes[0].old_value == "integer"
        assert type_changes[0].new_value == "string"


class TestComponentRequiredChanges:
    def test_optional_to_required(self):
        old = [_comp(
            properties={"name": {"type": "string"}},
            required=[],
        )]
        new = [_comp(
            properties={"name": {"type": "string"}},
            required=["name"],
        )]

        changes = compare_components(old, new)

        req_changes = [c for c in changes if c.type == COMPONENT_REQUIRED_CHANGED]
        assert len(req_changes) == 1
        assert req_changes[0].severity == "breaking"
        assert req_changes[0].old_value == "optional"
        assert req_changes[0].new_value == "required"

    def test_required_to_optional(self):
        old = [_comp(
            properties={"name": {"type": "string"}},
            required=["name"],
        )]
        new = [_comp(
            properties={"name": {"type": "string"}},
            required=[],
        )]

        changes = compare_components(old, new)

        req_changes = [c for c in changes if c.type == COMPONENT_REQUIRED_CHANGED]
        assert len(req_changes) == 1
        assert req_changes[0].severity == "non_breaking"


class TestComponentEdgeCases:
    def test_empty_components(self):
        changes = compare_components([], [])
        assert len(changes) == 0

    def test_null_properties(self):
        old = [_comp(properties=None)]
        new = [_comp(properties=None)]

        changes = compare_components(old, new)
        assert len(changes) == 0

    def test_null_required(self):
        old = [_comp(properties={"a": {"type": "string"}}, required=None)]
        new = [_comp(properties={"a": {"type": "string"}}, required=None)]

        changes = compare_components(old, new)
        assert len(changes) == 0

    def test_multiple_components(self):
        old = [
            _comp(name="User", properties={"id": {"type": "integer"}}),
            _comp(name="Email", properties={"address": {"type": "string"}}),
        ]
        new = [
            _comp(name="User", properties={"id": {"type": "integer"}}),
            _comp(name="Address", properties={"street": {"type": "string"}}),
        ]

        changes = compare_components(old, new)

        added = [c for c in changes if c.type == COMPONENT_ADDED]
        removed = [c for c in changes if c.type == COMPONENT_REMOVED]

        assert len(added) == 1
        assert added[0].component == "Address"
        assert len(removed) == 1
        assert removed[0].component == "Email"
