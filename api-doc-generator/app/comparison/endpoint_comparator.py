"""Compares endpoints between two API versions and detects changes."""

from typing import Any

from app.comparison.change_types import (
    BREAKING,
    NON_BREAKING,
    INFORMATIONAL,
    ENDPOINT_ADDED,
    ENDPOINT_REMOVED,
    PARAMETER_ADDED,
    REQUIRED_PARAMETER_ADDED,
    PARAMETER_REMOVED,
    PARAMETER_TYPE_CHANGED,
    PARAMETER_CONSTRAINT_CHANGED,
    REQUEST_BODY_ADDED,
    REQUEST_BODY_REMOVED,
    REQUEST_BODY_TYPE_CHANGED,
    REQUEST_BODY_PROPERTY_ADDED,
    REQUEST_BODY_REQUIRED_PROPERTY_ADDED,
    REQUEST_BODY_PROPERTY_REMOVED,
    REQUEST_BODY_PROPERTY_TYPE_CHANGED,
    RESPONSE_STATUS_ADDED,
    RESPONSE_STATUS_REMOVED,
    RESPONSE_SCHEMA_TYPE_CHANGED,
    RESPONSE_PROPERTY_ADDED,
    RESPONSE_PROPERTY_REMOVED,
    RESPONSE_PROPERTY_TYPE_CHANGED,
    SUMMARY_CHANGED,
    DESCRIPTION_CHANGED,
    SECURITY_CHANGED,
)
from app.comparison.schema_comparator import (
    compare_object_properties,
    compare_schema_constraints,
)
from app.schemas.comparison import Change


def _endpoint_key(endpoint: Any) -> str:
    """Create a unique identity key for an endpoint using METHOD + PATH."""
    method = (endpoint.method or "").upper()
    path = endpoint.path or ""
    return f"{method} {path}"


def compare_endpoints(
    old_endpoints: list[Any],
    new_endpoints: list[Any],
) -> list[Change]:
    """Compare two sets of endpoints and return all detected changes.

    Endpoints are matched by METHOD + PATH identity.
    """
    changes: list[Change] = []

    old_map: dict[str, Any] = {_endpoint_key(e): e for e in old_endpoints}
    new_map: dict[str, Any] = {_endpoint_key(e): e for e in new_endpoints}

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    # Added endpoints
    for key in sorted(new_keys - old_keys):
        ep = new_map[key]
        changes.append(Change(
            type=ENDPOINT_ADDED,
            severity=NON_BREAKING,
            method=ep.method.upper(),
            path=ep.path,
            message=f"Endpoint {ep.method.upper()} {ep.path} was added.",
        ))

    # Removed endpoints
    for key in sorted(old_keys - new_keys):
        ep = old_map[key]
        changes.append(Change(
            type=ENDPOINT_REMOVED,
            severity=BREAKING,
            method=ep.method.upper(),
            path=ep.path,
            message=f"Endpoint {ep.method.upper()} {ep.path} was removed.",
        ))

    # Modified endpoints
    for key in sorted(old_keys & new_keys):
        old_ep = old_map[key]
        new_ep = new_map[key]
        method = old_ep.method.upper()
        path = old_ep.path

        changes.extend(_compare_metadata(old_ep, new_ep, method, path))
        changes.extend(_compare_parameters(old_ep, new_ep, method, path))
        changes.extend(_compare_request_body(old_ep, new_ep, method, path))
        changes.extend(_compare_responses(old_ep, new_ep, method, path))
        changes.extend(_compare_security(old_ep, new_ep, method, path))

    return changes


def _compare_metadata(
    old_ep: Any,
    new_ep: Any,
    method: str,
    path: str,
) -> list[Change]:
    """Compare summary and description (informational changes)."""
    changes: list[Change] = []

    if (old_ep.summary or "") != (new_ep.summary or ""):
        changes.append(Change(
            type=SUMMARY_CHANGED,
            severity=INFORMATIONAL,
            method=method,
            path=path,
            field="summary",
            old_value=old_ep.summary,
            new_value=new_ep.summary,
            message=f"Summary changed for {method} {path}.",
        ))

    if (old_ep.description or "") != (new_ep.description or ""):
        changes.append(Change(
            type=DESCRIPTION_CHANGED,
            severity=INFORMATIONAL,
            method=method,
            path=path,
            field="description",
            old_value=old_ep.description,
            new_value=new_ep.description,
            message=f"Description changed for {method} {path}.",
        ))

    return changes


def _compare_parameters(
    old_ep: Any,
    new_ep: Any,
    method: str,
    path: str,
) -> list[Change]:
    """Compare request parameters between two endpoint versions."""
    changes: list[Change] = []

    old_params = _params_by_name(old_ep.parameters)
    new_params = _params_by_name(new_ep.parameters)

    old_names = set(old_params.keys())
    new_names = set(new_params.keys())

    # Added parameters
    for name in sorted(new_names - old_names):
        param = new_params[name]
        is_required = param.get("required", False)

        if is_required:
            changes.append(Change(
                type=REQUIRED_PARAMETER_ADDED,
                severity=BREAKING,
                method=method,
                path=path,
                field=name,
                message=f"Required parameter '{name}' was added to {method} {path}.",
            ))
        else:
            changes.append(Change(
                type=PARAMETER_ADDED,
                severity=NON_BREAKING,
                method=method,
                path=path,
                field=name,
                message=f"Optional parameter '{name}' was added to {method} {path}.",
            ))

    # Removed parameters
    for name in sorted(old_names - new_names):
        changes.append(Change(
            type=PARAMETER_REMOVED,
            severity=NON_BREAKING,
            method=method,
            path=path,
            field=name,
            message=f"Parameter '{name}' was removed from {method} {path}.",
        ))

    # Modified parameters
    for name in sorted(old_names & new_names):
        old_param = old_params[name]
        new_param = new_params[name]

        old_schema = old_param.get("schema", {}) or {}
        new_schema = new_param.get("schema", {}) or {}

        # Type change
        old_type = old_schema.get("type")
        new_type = new_schema.get("type")
        if old_type != new_type:
            changes.append(Change(
                type=PARAMETER_TYPE_CHANGED,
                severity=BREAKING,
                method=method,
                path=path,
                field=name,
                old_value=old_type,
                new_value=new_type,
                message=f"Parameter '{name}' type changed from '{old_type}' to '{new_type}' in {method} {path}.",
            ))

        # Constraint changes
        for constraint_change in compare_schema_constraints(old_schema, new_schema):
            changes.append(Change(
                type=PARAMETER_CONSTRAINT_CHANGED,
                severity=constraint_change["severity"],
                method=method,
                path=path,
                field=f"{name}.{constraint_change['field']}",
                old_value=constraint_change["old_value"],
                new_value=constraint_change["new_value"],
                message=f"Parameter '{name}' {constraint_change['message']} in {method} {path}.",
            ))

    return changes


def _compare_request_body(
    old_ep: Any,
    new_ep: Any,
    method: str,
    path: str,
) -> list[Change]:
    """Compare request body schemas between two endpoint versions."""
    changes: list[Change] = []

    old_body = old_ep.request_body
    new_body = new_ep.request_body

    if old_body is None and new_body is not None:
        changes.append(Change(
            type=REQUEST_BODY_ADDED,
            severity=NON_BREAKING,
            method=method,
            path=path,
            message=f"Request body was added to {method} {path}.",
        ))
        return changes

    if old_body is not None and new_body is None:
        changes.append(Change(
            type=REQUEST_BODY_REMOVED,
            severity=BREAKING,
            method=method,
            path=path,
            message=f"Request body was removed from {method} {path}.",
        ))
        return changes

    if old_body is None and new_body is None:
        return changes

    old_schema = _extract_body_schema(old_body)
    new_schema = _extract_body_schema(new_body)

    # Type change
    old_type = (old_schema or {}).get("type")
    new_type = (new_schema or {}).get("type")

    if old_type != new_type and old_type is not None and new_type is not None:
        changes.append(Change(
            type=REQUEST_BODY_TYPE_CHANGED,
            severity=BREAKING,
            method=method,
            path=path,
            old_value=old_type,
            new_value=new_type,
            message=f"Request body type changed from '{old_type}' to '{new_type}' in {method} {path}.",
        ))
        return changes

    # Property changes for object schemas
    prop_changes = compare_object_properties(old_schema, new_schema, context="request")
    for pc in prop_changes:
        change_type = _map_request_body_change_type(pc)
        changes.append(Change(
            type=change_type,
            severity=pc["severity"],
            method=method,
            path=path,
            field=pc["field"],
            old_value=pc["old_value"],
            new_value=pc["new_value"],
            message=f"{pc['message']} In request body of {method} {path}.",
        ))

    return changes


def _compare_responses(
    old_ep: Any,
    new_ep: Any,
    method: str,
    path: str,
) -> list[Change]:
    """Compare response definitions between two endpoint versions."""
    changes: list[Change] = []

    old_responses = old_ep.responses or {}
    new_responses = new_ep.responses or {}

    old_statuses = set(old_responses.keys())
    new_statuses = set(new_responses.keys())

    # Added response statuses
    for status in sorted(new_statuses - old_statuses):
        changes.append(Change(
            type=RESPONSE_STATUS_ADDED,
            severity=NON_BREAKING,
            method=method,
            path=path,
            field=status,
            message=f"Response status '{status}' was added to {method} {path}.",
        ))

    # Removed response statuses
    for status in sorted(old_statuses - new_statuses):
        changes.append(Change(
            type=RESPONSE_STATUS_REMOVED,
            severity=BREAKING,
            method=method,
            path=path,
            field=status,
            message=f"Response status '{status}' was removed from {method} {path}.",
        ))

    # Modified responses
    for status in sorted(old_statuses & new_statuses):
        old_resp = old_responses[status]
        new_resp = new_responses[status]

        old_schema = _extract_response_schema(old_resp)
        new_schema = _extract_response_schema(new_resp)

        if old_schema is None and new_schema is None:
            continue

        # Type change
        old_type = (old_schema or {}).get("type")
        new_type = (new_schema or {}).get("type")

        if old_type != new_type and old_type is not None and new_type is not None:
            changes.append(Change(
                type=RESPONSE_SCHEMA_TYPE_CHANGED,
                severity=BREAKING,
                method=method,
                path=path,
                field=status,
                old_value=old_type,
                new_value=new_type,
                message=f"Response '{status}' schema type changed from '{old_type}' to '{new_type}' in {method} {path}.",
            ))
            continue

        # Property changes for object responses
        prop_changes = compare_object_properties(old_schema, new_schema, context="response")
        for pc in prop_changes:
            change_type = _map_response_change_type(pc)
            changes.append(Change(
                type=change_type,
                severity=pc["severity"],
                method=method,
                path=path,
                field=f"{status}.{pc['field']}",
                old_value=pc["old_value"],
                new_value=pc["new_value"],
                message=f"{pc['message']} In response '{status}' of {method} {path}.",
            ))

    return changes


def _compare_security(
    old_ep: Any,
    new_ep: Any,
    method: str,
    path: str,
) -> list[Change]:
    """Compare security requirements between two endpoint versions."""
    changes: list[Change] = []

    old_security = old_ep.security or []
    new_security = new_ep.security or []

    if old_security != new_security:
        changes.append(Change(
            type=SECURITY_CHANGED,
            severity=BREAKING,
            method=method,
            path=path,
            field="security",
            old_value=old_security if old_security else None,
            new_value=new_security if new_security else None,
            message=f"Security requirements changed for {method} {path}.",
        ))

    return changes


def _params_by_name(params: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    """Index parameters by name for comparison."""
    if not params:
        return {}
    return {p.get("name", ""): p for p in params if isinstance(p, dict)}


def _extract_body_schema(body: dict[str, Any] | None) -> dict[str, Any] | None:
    """Extract the schema from a request body, looking inside content/application/json."""
    if not body:
        return None

    content = body.get("content", {})
    if not content:
        return body.get("schema")

    for media_type in ("application/json", "application/xml", "text/plain"):
        if media_type in content:
            return content[media_type].get("schema")

    # Fall back to first content type
    for _key, value in content.items():
        if isinstance(value, dict):
            return value.get("schema")

    return None


def _extract_response_schema(response: dict[str, Any] | None) -> dict[str, Any] | None:
    """Extract the schema from a response definition."""
    if not response:
        return None

    content = response.get("content", {})
    if not content:
        return response.get("schema")

    for media_type in ("application/json", "application/xml", "text/plain"):
        if media_type in content:
            return content[media_type].get("schema")

    for _key, value in content.items():
        if isinstance(value, dict):
            return value.get("schema")

    return None


def _map_request_body_change_type(prop_change: dict[str, Any]) -> str:
    """Map a property change dict to a request body change type constant."""
    msg = prop_change["message"]
    if "Required property" in msg:
        return REQUEST_BODY_REQUIRED_PROPERTY_ADDED
    if "Optional property" in msg:
        return REQUEST_BODY_PROPERTY_ADDED
    if "removed" in msg.lower():
        return REQUEST_BODY_PROPERTY_REMOVED
    if "type changed" in msg.lower():
        return REQUEST_BODY_PROPERTY_TYPE_CHANGED
    return REQUEST_BODY_PROPERTY_ADDED


def _map_response_change_type(prop_change: dict[str, Any]) -> str:
    """Map a property change dict to a response change type constant."""
    msg = prop_change["message"]
    if "added" in msg.lower():
        return RESPONSE_PROPERTY_ADDED
    if "removed" in msg.lower():
        return RESPONSE_PROPERTY_REMOVED
    if "type changed" in msg.lower():
        return RESPONSE_PROPERTY_TYPE_CHANGED
    return RESPONSE_PROPERTY_ADDED
