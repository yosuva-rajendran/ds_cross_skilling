"""Tests for FastAPI source code parser."""

from app.parsers.fastapi_parser import parse_fastapi_source


SAMPLE_SOURCE = '''
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    """A user creation request."""
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


@router.get("/users/{user_id}", summary="Get a user", tags=["users"])
def get_user(user_id: int, verbose: bool = False):
    """Retrieve a user by their ID."""
    pass


@router.post("/users", summary="Create a user", response_model=UserResponse, tags=["users"])
def create_user(body: UserCreate):
    """Create a new user."""
    pass


@router.delete("/users/{user_id}", summary="Delete a user")
async def delete_user(user_id: int):
    """Delete a user by their ID."""
    pass
'''


class TestParseEndpoints:
    def test_extracts_all_endpoints(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)

        assert len(result["endpoints"]) == 3

    def test_get_endpoint(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        endpoints = {ep["method"]: ep for ep in result["endpoints"]}

        get_ep = endpoints["GET"]
        assert get_ep["path"] == "/users/{user_id}"
        assert get_ep["summary"] == "Get a user"
        assert get_ep["description"] == "Retrieve a user by their ID."
        assert get_ep["tags"] == ["users"]

    def test_post_endpoint_with_request_body(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        endpoints = {ep["method"]: ep for ep in result["endpoints"]}

        post_ep = endpoints["POST"]
        assert post_ep["path"] == "/users"
        assert post_ep["request_body"] is not None

        schema = post_ep["request_body"]["content"]["application/json"]["schema"]
        assert "name" in schema["properties"]
        assert "email" in schema["properties"]

    def test_delete_endpoint(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        endpoints = {ep["method"]: ep for ep in result["endpoints"]}

        del_ep = endpoints["DELETE"]
        assert del_ep["path"] == "/users/{user_id}"
        assert del_ep["summary"] == "Delete a user"

    def test_path_parameters(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        endpoints = {ep["method"]: ep for ep in result["endpoints"]}

        get_ep = endpoints["GET"]
        params = get_ep["parameters"]

        path_param = next(p for p in params if p["name"] == "user_id")
        assert path_param["in"] == "path"
        assert path_param["required"] is True
        assert path_param["schema"]["type"] == "integer"

    def test_query_parameters(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        endpoints = {ep["method"]: ep for ep in result["endpoints"]}

        get_ep = endpoints["GET"]
        params = get_ep["parameters"]

        query_param = next(p for p in params if p["name"] == "verbose")
        assert query_param["in"] == "query"
        assert query_param["required"] is False
        assert query_param["schema"]["type"] == "boolean"

    def test_response_model(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        endpoints = {ep["method"]: ep for ep in result["endpoints"]}

        post_ep = endpoints["POST"]
        assert post_ep["responses"] is not None
        assert "200" in post_ep["responses"]


class TestParseComponents:
    def test_extracts_pydantic_models(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)

        assert len(result["components"]) == 2

    def test_model_properties(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        components = {c["name"]: c for c in result["components"]}

        user_create = components["UserCreate"]
        assert "name" in user_create["properties"]
        assert "email" in user_create["properties"]
        assert user_create["properties"]["name"]["type"] == "string"

    def test_required_fields(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        components = {c["name"]: c for c in result["components"]}

        user_create = components["UserCreate"]
        assert "name" in user_create["required"]
        assert "email" in user_create["required"]

    def test_model_description(self):
        result = parse_fastapi_source(SAMPLE_SOURCE)
        components = {c["name"]: c for c in result["components"]}

        user_create = components["UserCreate"]
        assert user_create["description"] == "A user creation request."


class TestEdgeCases:
    def test_empty_source(self):
        result = parse_fastapi_source("")
        assert result["endpoints"] == []
        assert result["components"] == []

    def test_no_routes(self):
        source = "x = 1\ny = 2\n"
        result = parse_fastapi_source(source)
        assert result["endpoints"] == []

    def test_non_fastapi_decorators_ignored(self):
        source = '''
@some_decorator
def foo():
    pass

@property
def bar(self):
    pass
'''
        result = parse_fastapi_source(source)
        assert result["endpoints"] == []
