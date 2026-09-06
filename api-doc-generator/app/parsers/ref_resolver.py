from typing import Any


def resolve_ref(ref: str, spec: dict[str, Any]) -> Any:
    if not ref.startswith("#/"):
        raise ValueError(f"External references are not supported: {ref}")

    parts = ref[2:].split("/")

    current: Any = spec

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Reference not found: {ref}")

        current = current[part]

    return current


def resolve_refs(value: Any, spec: dict[str, Any]) -> Any:
    """
    Recursively resolve all internal $ref values.
    """

    if isinstance(value, dict):

        # If this object is a reference
        if "$ref" in value:
            resolved = resolve_ref(value["$ref"], spec)

            # Resolve references inside the referenced object too
            return resolve_refs(resolved, spec)

        return {
            key: resolve_refs(item, spec)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            resolve_refs(item, spec)
            for item in value
        ]

    return value