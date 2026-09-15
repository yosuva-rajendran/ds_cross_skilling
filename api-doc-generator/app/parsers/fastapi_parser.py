import ast
import re
from typing import Any


PYTHON_TYPE_MAP = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "List": "array",
    "Dict": "object",
    "Optional": "string",
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def parse_fastapi_source(source_code: str) -> dict[str, Any]:
    """Parse a FastAPI source file and return endpoints + components in the same
    shape as openapi_parser, so the ingestion pipeline can reuse everything downstream."""
    tree = ast.parse(source_code)

    models = _extract_pydantic_models(tree)
    endpoints = _extract_endpoints(tree, models)

    components = [
        {
            "name": name,
            "description": info.get("description"),
            "schema_type": "object",
            "properties": info.get("properties", {}),
            "required": info.get("required", []),
        }
        for name, info in models.items()
    ]

    return {
        "endpoints": endpoints,
        "components": components,
    }


def _extract_pydantic_models(tree: ast.Module) -> dict[str, dict[str, Any]]:
    models: dict[str, dict[str, Any]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        is_base_model = any(
            _get_name(base) in ("BaseModel", "SQLModel")
            for base in node.bases
        )
        if not is_base_model:
            continue

        properties: dict[str, Any] = {}
        required: list[str] = []
        description = ast.get_docstring(node)

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_type = _annotation_to_openapi_type(item.annotation)

                properties[field_name] = {"type": field_type}

                if item.value is None:
                    required.append(field_name)

        models[node.name] = {
            "description": description,
            "properties": properties,
            "required": required,
        }

    return models


def _extract_endpoints(
    tree: ast.Module,
    models: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            route_info = _parse_route_decorator(decorator)
            if not route_info:
                continue

            method = route_info["method"]
            path = route_info["path"]
            summary = route_info.get("summary")
            tags = route_info.get("tags")
            description = ast.get_docstring(node)

            parameters, request_body = _extract_function_params(
                node, path, models
            )

            response_model_name = route_info.get("response_model")
            responses = None
            if response_model_name and response_model_name in models:
                model_info = models[response_model_name]
                responses = {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": model_info.get("properties", {}),
                                }
                            }
                        },
                    }
                }

            endpoints.append({
                "path": path,
                "method": method.upper(),
                "tags": tags,
                "summary": summary,
                "description": description,
                "operation_id": node.name,
                "parameters": parameters if parameters else None,
                "request_body": request_body,
                "responses": responses,
                "security": None,
            })

    return endpoints


def _parse_route_decorator(decorator: ast.expr) -> dict[str, Any] | None:
    if not isinstance(decorator, ast.Call):
        return None

    func = decorator.func
    if isinstance(func, ast.Attribute) and func.attr in HTTP_METHODS:
        method = func.attr
    else:
        return None

    if not decorator.args:
        return None

    path_node = decorator.args[0]
    if not isinstance(path_node, ast.Constant) or not isinstance(path_node.value, str):
        return None

    path = path_node.value
    result: dict[str, Any] = {"method": method, "path": path}

    for kw in decorator.keywords:
        if kw.arg == "summary" and isinstance(kw.value, ast.Constant):
            result["summary"] = kw.value.value
        elif kw.arg == "tags" and isinstance(kw.value, ast.List):
            result["tags"] = [
                elt.value for elt in kw.value.elts
                if isinstance(elt, ast.Constant)
            ]
        elif kw.arg == "response_model":
            result["response_model"] = _get_name(kw.value)

    return result


def _extract_function_params(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    path: str,
    models: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    parameters: list[dict[str, Any]] = []
    request_body = None

    path_params = set()
    for match in re.finditer(r"\{(\w+)\}", path):
        path_params.add(match.group(1))

    for arg in func_node.args.args:
        name = arg.arg

        if name in ("self", "cls", "request", "response", "session", "db"):
            continue

        type_name = _get_annotation_name(arg.annotation) if arg.annotation else None
        openapi_type = _annotation_to_openapi_type(arg.annotation) if arg.annotation else "string"

        if type_name and type_name in models:
            model_info = models[type_name]
            request_body = {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": model_info.get("properties", {}),
                            "required": model_info.get("required", []),
                        }
                    }
                }
            }
            continue

        param_in = "path" if name in path_params else "query"
        is_required = name in path_params

        defaults = func_node.args.defaults
        args_list = func_node.args.args
        num_defaults = len(defaults)
        num_args = len(args_list)
        arg_index = args_list.index(arg)
        default_index = arg_index - (num_args - num_defaults)

        has_default = default_index >= 0
        if has_default and not is_required:
            is_required = False
        elif param_in == "query" and not has_default:
            is_required = True

        parameters.append({
            "name": name,
            "in": param_in,
            "required": is_required,
            "schema": {"type": openapi_type},
        })

    return parameters, request_body


def _annotation_to_openapi_type(annotation: ast.expr | None) -> str:
    if annotation is None:
        return "string"

    name = _get_annotation_name(annotation)
    return PYTHON_TYPE_MAP.get(name, "string")


def _get_annotation_name(annotation: ast.expr | None) -> str | None:
    if annotation is None:
        return None
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Constant):
        return str(annotation.value)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    if isinstance(annotation, ast.Subscript):
        return _get_annotation_name(annotation.value)
    return None


def _get_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
