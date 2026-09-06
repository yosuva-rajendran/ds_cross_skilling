from typing import Any

from app.parsers.ref_resolver import resolve_refs


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
}


def parse_openapi(spec: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        path_parameters = path_item.get("parameters", [])

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue

            operation_parameters = operation.get("parameters", [])

            parameters = path_parameters + operation_parameters

            request_body = operation.get("requestBody")
            responses = operation.get("responses")

            endpoints.append({
                "path": path,
                "method": method.upper(),
                "tags": operation.get("tags"),
                "summary": operation.get("summary"),
                "description": operation.get("description"),
                "operation_id": operation.get("operationId"),

                "parameters": resolve_refs(
                    parameters,
                    spec,
                ) if parameters else None,

                "request_body": resolve_refs(
                    request_body,
                    spec,
                ) if request_body else None,

                "responses": resolve_refs(
                    responses,
                    spec,
                ) if responses else None,

                "security": operation.get("security"),
            })

    return endpoints