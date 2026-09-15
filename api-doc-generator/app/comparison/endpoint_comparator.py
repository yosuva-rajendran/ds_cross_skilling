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
    return f"{(endpoint.method or '').upper()} {endpoint.path or ''}"


def compare_endpoints(
    old_endpoints: list[Any],
    new_endpoints: list[Any],
) -> list[Change]:
    changes: list[Change] = []

    old_map = {_endpoint_key(e): e for e in old_endpoints}
    new_map = {_endpoint_key(e): e for e in new_endpoints}

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    for key in sorted(new_keys - old_keys):
        ep = new_map[key]
        changes.append(Change(
            type=ENDPOINT_ADDED, severity=NON_BREAKING,
            method=ep.method.upper(), path=ep.path,
            message=f"Endpoint {ep.method.upper()} {ep.path} was added.",
        ))

    for key in sorted(old_keys - new_keys):
        ep = old_map[key]
        changes.append(Change(
            type=ENDPOINT_REMOVED, severity=BREAKING,
            method=ep.method.upper(), path=ep.path,
            message=f"Endpoint {ep.method.upper()} {ep.path} was removed.",
        ))

    for key in sorted(old_keys & new_keys):
        old_ep, new_ep = old_map[key], new_map[key]
        method, path = old_ep.method.upper(), old_ep.path

        changes.extend(_compare_metadata(old_ep, new_ep, method, path))
        changes.extend(_compare_parameters(old_ep, new_ep, method, path))
        changes.extend(_compare_request_body(old_ep, new_ep, method, path))
        changes.extend(_compare_responses(old_ep, new_ep, method, path))
        changes.extend(_compare_security(old_ep, new_ep, method, path))

    return changes


def _compare_metadata(old_ep: Any, new_ep: Any, method: str, path: str) -> list[Change]:
    changes: list[Change] = []

    if (old_ep.summary or "") != (new_ep.summary or ""):
        changes.append(Change(
            type=SUMMARY_CHANGED, severity=INFORMATIONAL,
            method=method, path=path, field="summary",
            old_value=old_ep.summary, new_value=new_ep.summary,
            message=f"Summary changed for {method} {path}.",
        ))

    if (old_ep.description or "") != (new_ep.description or ""):
        changes.append(Change(
            type=DESCRIPTION_CHANGED, severity=INFORMATIONAL,
            method=method, path=path, field="description",
            old_value=old_ep.description, new_value=new_ep.description,
            message=f"Description changed for {method} {path}.",
        ))

    return changes


def _compare_parameters(old_ep: Any, new_ep: Any, method: str, path: str) -> list[Change]:
    changes: list[Change] = []

    old_params = _params_by_name(old_ep.parameters)
    new_params = _params_by_name(new_ep.parameters)
    old_names = set(old_params.keys())
    new_names = set(new_params.keys())

    for name in sorted(new_names - old_names):
        is_required = new_params[name].get("required", False)
        changes.append(Change(
            type=REQUIRED_PARAMETER_ADDED if is_required else PARAMETER_ADDED,
            severity=BREAKING if is_required else NON_BREAKING,
            method=method, path=path, field=name,
            message=f"{'Required' if is_required else 'Optional'} parameter '{name}' was added to {method} {path}.",
        ))

    for name in sorted(old_names - new_names):
        changes.append(Change(
            type=PARAMETER_REMOVED, severity=NON_BREAKING,
            method=method, path=path, field=name,
            message=f"Parameter '{name}' was removed from {method} {path}.",
        ))

    for name in sorted(old_names & new_names):
        old_schema = old_params[name].get("schema", {}) or {}
        new_schema = new_params[name].get("schema", {}) or {}

        old_type = old_schema.get("type")
        new_type = new_schema.get("type")
        if old_type != new_type:
            changes.append(Change(
                type=PARAMETER_TYPE_CHANGED, severity=BREAKING,
                method=method, path=path, field=name,
                old_value=old_type, new_value=new_type,
                message=f"Parameter '{name}' type changed from '{old_type}' to '{new_type}' in {method} {path}.",
            ))

        for cc in compare_schema_constraints(old_schema, new_schema):
            changes.append(Change(
                type=PARAMETER_CONSTRAINT_CHANGED, severity=cc["severity"],
                method=method, path=path,
                field=f"{name}.{cc['field']}",
                old_value=cc["old_value"], new_value=cc["new_value"],
                message=f"Parameter '{name}' {cc['message']} in {method} {path}.",
            ))

    return changes


def _compare_request_body(old_ep: Any, new_ep: Any, method: str, path: str) -> list[Change]:
    changes: list[Change] = []
    old_body, new_body = old_ep.request_body, new_ep.request_body

    if old_body is None and new_body is not None:
        changes.append(Change(
            type=REQUEST_BODY_ADDED, severity=NON_BREAKING,
            method=method, path=path,
            message=f"Request body was added to {method} {path}.",
        ))
        return changes

    if old_body is not None and new_body is None:
        changes.append(Change(
            type=REQUEST_BODY_REMOVED, severity=BREAKING,
            method=method, path=path,
            message=f"Request body was removed from {method} {path}.",
        ))
        return changes

    if old_body is None and new_body is None:
        return changes

    old_schema = _extract_content_schema(old_body)
    new_schema = _extract_content_schema(new_body)

    old_type = (old_schema or {}).get("type")
    new_type = (new_schema or {}).get("type")
    if old_type != new_type and old_type is not None and new_type is not None:
        changes.append(Change(
            type=REQUEST_BODY_TYPE_CHANGED, severity=BREAKING,
            method=method, path=path,
            old_value=old_type, new_value=new_type,
            message=f"Request body type changed from '{old_type}' to '{new_type}' in {method} {path}.",
        ))
        return changes

    _KIND_TO_TYPE = {
        "added": REQUEST_BODY_PROPERTY_ADDED,
        "removed": REQUEST_BODY_PROPERTY_REMOVED,
        "type_changed": REQUEST_BODY_PROPERTY_TYPE_CHANGED,
        "required_changed": REQUEST_BODY_PROPERTY_TYPE_CHANGED,
    }

    for pc in compare_object_properties(old_schema, new_schema, context="request"):
        if pc["kind"] == "added" and pc["severity"] == BREAKING:
            change_type = REQUEST_BODY_REQUIRED_PROPERTY_ADDED
        else:
            change_type = _KIND_TO_TYPE.get(pc["kind"], REQUEST_BODY_PROPERTY_ADDED)

        changes.append(Change(
            type=change_type, severity=pc["severity"],
            method=method, path=path, field=pc["field"],
            old_value=pc["old_value"], new_value=pc["new_value"],
            message=f"{pc['message']} In request body of {method} {path}.",
        ))

    return changes


def _compare_responses(old_ep: Any, new_ep: Any, method: str, path: str) -> list[Change]:
    changes: list[Change] = []
    old_responses = old_ep.responses or {}
    new_responses = new_ep.responses or {}

    old_statuses = set(old_responses.keys())
    new_statuses = set(new_responses.keys())

    for status in sorted(new_statuses - old_statuses):
        changes.append(Change(
            type=RESPONSE_STATUS_ADDED, severity=NON_BREAKING,
            method=method, path=path, field=status,
            message=f"Response status '{status}' was added to {method} {path}.",
        ))

    for status in sorted(old_statuses - new_statuses):
        changes.append(Change(
            type=RESPONSE_STATUS_REMOVED, severity=BREAKING,
            method=method, path=path, field=status,
            message=f"Response status '{status}' was removed from {method} {path}.",
        ))

    _KIND_TO_TYPE = {
        "added": RESPONSE_PROPERTY_ADDED,
        "removed": RESPONSE_PROPERTY_REMOVED,
        "type_changed": RESPONSE_PROPERTY_TYPE_CHANGED,
        "required_changed": RESPONSE_PROPERTY_ADDED,
    }

    for status in sorted(old_statuses & new_statuses):
        old_schema = _extract_content_schema(old_responses[status])
        new_schema = _extract_content_schema(new_responses[status])

        if old_schema is None and new_schema is None:
            continue

        old_type = (old_schema or {}).get("type")
        new_type = (new_schema or {}).get("type")
        if old_type != new_type and old_type is not None and new_type is not None:
            changes.append(Change(
                type=RESPONSE_SCHEMA_TYPE_CHANGED, severity=BREAKING,
                method=method, path=path, field=status,
                old_value=old_type, new_value=new_type,
                message=f"Response '{status}' schema type changed from '{old_type}' to '{new_type}' in {method} {path}.",
            ))
            continue

        for pc in compare_object_properties(old_schema, new_schema, context="response"):
            change_type = _KIND_TO_TYPE.get(pc["kind"], RESPONSE_PROPERTY_ADDED)
            changes.append(Change(
                type=change_type, severity=pc["severity"],
                method=method, path=path,
                field=f"{status}.{pc['field']}",
                old_value=pc["old_value"], new_value=pc["new_value"],
                message=f"{pc['message']} In response '{status}' of {method} {path}.",
            ))

    return changes


def _compare_security(old_ep: Any, new_ep: Any, method: str, path: str) -> list[Change]:
    old_security = old_ep.security or []
    new_security = new_ep.security or []

    if old_security != new_security:
        return [Change(
            type=SECURITY_CHANGED, severity=BREAKING,
            method=method, path=path, field="security",
            old_value=old_security or None, new_value=new_security or None,
            message=f"Security requirements changed for {method} {path}.",
        )]
    return []


def _params_by_name(params: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if not params:
        return {}
    return {p.get("name", ""): p for p in params if isinstance(p, dict)}


def _extract_content_schema(obj: dict[str, Any] | None) -> dict[str, Any] | None:
    if not obj:
        return None

    content = obj.get("content", {})
    if not content:
        return obj.get("schema")

    for media_type in ("application/json", "application/xml", "text/plain"):
        if media_type in content:
            return content[media_type].get("schema")

    for value in content.values():
        if isinstance(value, dict):
            return value.get("schema")

    return None
