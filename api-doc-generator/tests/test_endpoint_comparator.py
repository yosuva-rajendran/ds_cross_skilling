"""Tests for endpoint comparison logic."""

import pytest
from types import SimpleNamespace

from app.comparison.endpoint_comparator import compare_endpoints
from app.comparison.change_types import (
    ENDPOINT_ADDED,
    ENDPOINT_REMOVED,
    PARAMETER_ADDED,
    REQUIRED_PARAMETER_ADDED,
    PARAMETER_REMOVED,
    PARAMETER_TYPE_CHANGED,
    REQUEST_BODY_PROPERTY_ADDED,
    REQUEST_BODY_REQUIRED_PROPERTY_ADDED,
    REQUEST_BODY_PROPERTY_REMOVED,
    REQUEST_BODY_PROPERTY_TYPE_CHANGED,
    REQUEST_BODY_TYPE_CHANGED,
    RESPONSE_STATUS_ADDED,
    RESPONSE_STATUS_REMOVED,
    RESPONSE_SCHEMA_TYPE_CHANGED,
    RESPONSE_PROPERTY_ADDED,
    RESPONSE_PROPERTY_REMOVED,
    SUMMARY_CHANGED,
    DESCRIPTION_CHANGED,
)


def _ep(
    method="GET",
    path="/test",
    summary=None,
    description=None,
    parameters=None,
    request_body=None,
    responses=None,
    security=None,
):
    """Create a mock endpoint object."""
    return SimpleNamespace(
        method=method,
        path=path,
        summary=summary,
        description=description,
        parameters=parameters,
        request_body=request_body,
        responses=responses,
        security=security,
    )


# ── Endpoint added/removed ──


class TestEndpointAddedRemoved:
    def test_endpoint_added(self):
        old = []
        new = [_ep(method="GET", path="/users")]

        changes = compare_endpoints(old, new)

        assert len(changes) == 1
        assert changes[0].type == ENDPOINT_ADDED
        assert changes[0].severity == "non_breaking"
        assert changes[0].method == "GET"
        assert changes[0].path == "/users"

    def test_endpoint_removed(self):
        old = [_ep(method="DELETE", path="/users/{id}")]
        new = []

        changes = compare_endpoints(old, new)

        assert len(changes) == 1
        assert changes[0].type == ENDPOINT_REMOVED
        assert changes[0].severity == "breaking"

    def test_endpoint_unchanged(self):
        old = [_ep(method="GET", path="/users")]
        new = [_ep(method="GET", path="/users")]

        changes = compare_endpoints(old, new)

        assert len(changes) == 0

    def test_endpoint_description_changed(self):
        old = [_ep(method="GET", path="/users", description="Old desc")]
        new = [_ep(method="GET", path="/users", description="New desc")]

        changes = compare_endpoints(old, new)

        assert len(changes) == 1
        assert changes[0].type == DESCRIPTION_CHANGED
        assert changes[0].severity == "informational"

    def test_endpoint_summary_changed(self):
        old = [_ep(method="GET", path="/users", summary="Old")]
        new = [_ep(method="GET", path="/users", summary="New")]

        changes = compare_endpoints(old, new)

        desc_changes = [c for c in changes if c.type == SUMMARY_CHANGED]
        assert len(desc_changes) == 1
        assert desc_changes[0].severity == "informational"


# ── Parameter changes ──


class TestParameterChanges:
    def test_optional_parameter_added(self):
        old = [_ep(parameters=[{"name": "username", "required": True}])]
        new = [_ep(parameters=[
            {"name": "username", "required": True},
            {"name": "filter", "required": False},
        ])]

        changes = compare_endpoints(old, new)

        param_changes = [c for c in changes if c.type == PARAMETER_ADDED]
        assert len(param_changes) == 1
        assert param_changes[0].severity == "non_breaking"
        assert param_changes[0].field == "filter"

    def test_required_parameter_added(self):
        old = [_ep(parameters=[{"name": "username", "required": True}])]
        new = [_ep(parameters=[
            {"name": "username", "required": True},
            {"name": "tenant_id", "required": True},
        ])]

        changes = compare_endpoints(old, new)

        param_changes = [c for c in changes if c.type == REQUIRED_PARAMETER_ADDED]
        assert len(param_changes) == 1
        assert param_changes[0].severity == "breaking"
        assert param_changes[0].field == "tenant_id"

    def test_parameter_removed(self):
        old = [_ep(parameters=[
            {"name": "username", "required": True},
            {"name": "filter", "required": False},
        ])]
        new = [_ep(parameters=[{"name": "username", "required": True}])]

        changes = compare_endpoints(old, new)

        param_changes = [c for c in changes if c.type == PARAMETER_REMOVED]
        assert len(param_changes) == 1
        assert param_changes[0].severity == "non_breaking"

    def test_parameter_type_changed(self):
        old = [_ep(parameters=[
            {"name": "limit", "schema": {"type": "integer"}},
        ])]
        new = [_ep(parameters=[
            {"name": "limit", "schema": {"type": "string"}},
        ])]

        changes = compare_endpoints(old, new)

        type_changes = [c for c in changes if c.type == PARAMETER_TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].severity == "breaking"
        assert type_changes[0].old_value == "integer"
        assert type_changes[0].new_value == "string"


# ── Request body changes ──


class TestRequestBodyChanges:
    def test_request_body_property_added(self):
        old = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }}},
        })]
        new = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
            }}},
        })]

        changes = compare_endpoints(old, new)

        added = [c for c in changes if c.type == REQUEST_BODY_PROPERTY_ADDED]
        assert len(added) == 1
        assert added[0].severity == "non_breaking"
        assert added[0].field == "email"

    def test_request_body_required_property_added(self):
        old = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }}},
        })]
        new = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
            }}},
        })]

        changes = compare_endpoints(old, new)

        required_added = [c for c in changes if c.type == REQUEST_BODY_REQUIRED_PROPERTY_ADDED]
        assert len(required_added) == 1
        assert required_added[0].severity == "breaking"

    def test_request_body_property_removed(self):
        old = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
            }}},
        })]
        new = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }}},
        })]

        changes = compare_endpoints(old, new)

        removed = [c for c in changes if c.type == REQUEST_BODY_PROPERTY_REMOVED]
        assert len(removed) == 1
        assert removed[0].severity == "breaking"

    def test_request_body_type_changed(self):
        old = [_ep(request_body={
            "content": {"application/json": {"schema": {"type": "string"}}},
        })]
        new = [_ep(request_body={
            "content": {"application/json": {"schema": {"type": "integer"}}},
        })]

        changes = compare_endpoints(old, new)

        type_changes = [c for c in changes if c.type == REQUEST_BODY_TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].severity == "breaking"

    def test_request_body_property_type_changed(self):
        old = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"age": {"type": "integer"}},
            }}},
        })]
        new = [_ep(request_body={
            "content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"age": {"type": "string"}},
            }}},
        })]

        changes = compare_endpoints(old, new)

        type_changes = [c for c in changes if c.type == REQUEST_BODY_PROPERTY_TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].severity == "breaking"


# ── Response changes ──


class TestResponseChanges:
    def test_response_status_added(self):
        old = [_ep(responses={"200": {"description": "OK"}})]
        new = [_ep(responses={
            "200": {"description": "OK"},
            "404": {"description": "Not found"},
        })]

        changes = compare_endpoints(old, new)

        added = [c for c in changes if c.type == RESPONSE_STATUS_ADDED]
        assert len(added) == 1
        assert added[0].severity == "non_breaking"

    def test_response_status_removed(self):
        old = [_ep(responses={
            "200": {"description": "OK"},
            "404": {"description": "Not found"},
        })]
        new = [_ep(responses={"200": {"description": "OK"}})]

        changes = compare_endpoints(old, new)

        removed = [c for c in changes if c.type == RESPONSE_STATUS_REMOVED]
        assert len(removed) == 1
        assert removed[0].severity == "breaking"

    def test_response_schema_type_changed(self):
        old = [_ep(responses={
            "200": {"content": {"application/json": {"schema": {"type": "string"}}}},
        })]
        new = [_ep(responses={
            "200": {"content": {"application/json": {"schema": {"type": "object"}}}},
        })]

        changes = compare_endpoints(old, new)

        type_changes = [c for c in changes if c.type == RESPONSE_SCHEMA_TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].severity == "breaking"

    def test_response_property_added(self):
        old = [_ep(responses={
            "200": {"content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
            }}}},
        })]
        new = [_ep(responses={
            "200": {"content": {"application/json": {"schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string"},
                },
            }}}},
        })]

        changes = compare_endpoints(old, new)

        added = [c for c in changes if c.type == RESPONSE_PROPERTY_ADDED]
        assert len(added) == 1
        assert added[0].severity == "non_breaking"

    def test_response_property_removed(self):
        old = [_ep(responses={
            "200": {"content": {"application/json": {"schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                },
            }}}},
        })]
        new = [_ep(responses={
            "200": {"content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
            }}}},
        })]

        changes = compare_endpoints(old, new)

        removed = [c for c in changes if c.type == RESPONSE_PROPERTY_REMOVED]
        assert len(removed) == 1
        assert removed[0].severity == "breaking"


# ── Edge cases ──


class TestEdgeCases:
    def test_null_parameters(self):
        old = [_ep(parameters=None)]
        new = [_ep(parameters=None)]

        changes = compare_endpoints(old, new)
        assert len(changes) == 0

    def test_null_request_body(self):
        old = [_ep(request_body=None)]
        new = [_ep(request_body=None)]

        changes = compare_endpoints(old, new)
        assert len(changes) == 0

    def test_null_responses(self):
        old = [_ep(responses=None)]
        new = [_ep(responses=None)]

        changes = compare_endpoints(old, new)
        assert len(changes) == 0

    def test_empty_parameters_list(self):
        old = [_ep(parameters=[])]
        new = [_ep(parameters=[])]

        changes = compare_endpoints(old, new)
        assert len(changes) == 0

    def test_method_case_insensitive_matching(self):
        old = [_ep(method="get", path="/users")]
        new = [_ep(method="GET", path="/users")]

        changes = compare_endpoints(old, new)
        # Should match as same endpoint
        assert not any(c.type == ENDPOINT_ADDED for c in changes)
        assert not any(c.type == ENDPOINT_REMOVED for c in changes)

    def test_missing_schema_in_parameter(self):
        old = [_ep(parameters=[{"name": "q"}])]
        new = [_ep(parameters=[{"name": "q", "schema": {"type": "string"}}])]

        changes = compare_endpoints(old, new)
        type_changes = [c for c in changes if c.type == PARAMETER_TYPE_CHANGED]
        assert len(type_changes) == 1

    def test_multiple_endpoints_mixed_changes(self):
        old = [
            _ep(method="GET", path="/users"),
            _ep(method="POST", path="/users"),
        ]
        new = [
            _ep(method="GET", path="/users"),
            _ep(method="PUT", path="/users"),
        ]

        changes = compare_endpoints(old, new)

        added = [c for c in changes if c.type == ENDPOINT_ADDED]
        removed = [c for c in changes if c.type == ENDPOINT_REMOVED]

        assert len(added) == 1
        assert added[0].method == "PUT"
        assert len(removed) == 1
        assert removed[0].method == "POST"
