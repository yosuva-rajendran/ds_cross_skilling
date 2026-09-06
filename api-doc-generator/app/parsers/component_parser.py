from typing import Any

from app.parsers.ref_resolver import resolve_refs


def parse_components(spec: dict[str, Any]) -> list[dict[str, Any]]:
    components = spec.get("components", {})
    schemas = components.get("schemas", {})

    parsed_components = []

    for name, schema in schemas.items():

        resolved_schema = resolve_refs(schema, spec)

        parsed_components.append({
            "name": name,
            "description": resolved_schema.get("description"),
            "schema_type": resolved_schema.get("type"),
            "properties": resolved_schema.get("properties"),
            "required": resolved_schema.get("required"),
        })

    return parsed_components