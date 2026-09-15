from sqlmodel import Session

from app.models.api_version import APIVersion
from app.models.endpoint import Endpoint

from app.repositories.api_version_repository import APIVersionRepository
from app.repositories.endpoint_repository import EndpointRepository

from app.parsers.openapi_parser import parse_openapi
from app.parsers.component_parser import parse_components
from app.parsers.fastapi_parser import parse_fastapi_source

from app.services.openapi_service import OpenAPIService
from app.services.component_service import ComponentService


class IngestionService:
    def __init__(self, session: Session):
        self.endpoint_repository = EndpointRepository(session)
        self.api_version_repository = APIVersionRepository(session)
        self.component_service = ComponentService(session)

    def ingest_openapi(
        self,
        project_id: int,
        filename: str,
        content: bytes,
    ) -> dict:

        spec = OpenAPIService.load_file(
            filename,
            content,
        )

        version = spec.get("info", {}).get("version")

        if not version:
            raise ValueError(
                "OpenAPI specification must contain info.version"
            )

        api_version = APIVersion(
            project_id=project_id,
            version=version,
        )

        saved_version = self.api_version_repository.create(
            api_version
        )

        parsed_endpoints = parse_openapi(spec)

        endpoints = [
            Endpoint(
                project_id=project_id,
                version_id=saved_version.id,
                path=data["path"],
                method=data["method"],
                tags=data["tags"],
                summary=data["summary"],
                description=data["description"],
                operation_id=data["operation_id"],
                parameters=data["parameters"],
                request_body=data["request_body"],
                responses=data["responses"],
                security=data["security"],
            )
            for data in parsed_endpoints
        ]

        saved_endpoints = self.endpoint_repository.create_many(
            endpoints
        )

        parsed_components = parse_components(spec)

        saved_components = self.component_service.save_components(
        project_id=project_id,
        version_id=saved_version.id,
        parsed_components=parsed_components,
        )

        return {
            "version": saved_version,
            "endpoints": saved_endpoints,
            "components": saved_components,
        }

    def ingest_source_code(
        self,
        project_id: int,
        version: str,
        source_code: str,
    ) -> dict:
        api_version = APIVersion(
            project_id=project_id,
            version=version,
        )

        saved_version = self.api_version_repository.create(api_version)

        result = parse_fastapi_source(source_code)
        parsed_endpoints = result["endpoints"]
        parsed_components = result["components"]

        endpoints = [
            Endpoint(
                project_id=project_id,
                version_id=saved_version.id,
                path=data["path"],
                method=data["method"],
                tags=data.get("tags"),
                summary=data.get("summary"),
                description=data.get("description"),
                operation_id=data.get("operation_id"),
                parameters=data.get("parameters"),
                request_body=data.get("request_body"),
                responses=data.get("responses"),
                security=data.get("security"),
            )
            for data in parsed_endpoints
        ]

        saved_endpoints = self.endpoint_repository.create_many(endpoints)

        saved_components = self.component_service.save_components(
            project_id=project_id,
            version_id=saved_version.id,
            parsed_components=parsed_components,
        )

        return {
            "version": saved_version,
            "endpoints": saved_endpoints,
            "components": saved_components,
        }