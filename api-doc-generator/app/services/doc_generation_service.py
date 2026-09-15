import json

from openai import OpenAI
from sqlmodel import Session

from app.models.endpoint import Endpoint
from app.models.generated_doc import GeneratedDoc
from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.generated_doc_repository import GeneratedDocRepository
from app.schemas.generated_doc import EndpointDocumentation
from app.services.llm_client import get_llm_client, generate_structured


SYSTEM_PROMPT = (
    "You are an API documentation expert. "
    "Given structured information about an API endpoint, "
    "generate clear, accurate, developer-facing documentation. "
    "Be concise but complete."
)


class DocGenerationService:

    def __init__(self, session: Session, client: OpenAI | None = None):
        self.endpoint_repository = EndpointRepository(session)
        self.doc_repository = GeneratedDocRepository(session)
        self.client = client or get_llm_client()

    def generate_for_version(self, version_id: int) -> list[GeneratedDoc]:
        endpoints = self.endpoint_repository.get_by_version(version_id)
        return [self._generate_for_endpoint(ep) for ep in endpoints]

    def generate_for_endpoint_obj(self, endpoint: Endpoint) -> GeneratedDoc:
        return self._generate_for_endpoint(endpoint)

    def _generate_for_endpoint(self, endpoint: Endpoint) -> GeneratedDoc:

        existing = self.doc_repository.get_by_endpoint(endpoint.id)
        if existing:
            return existing

        endpoint_info = self._build_endpoint_context(endpoint)

        user_prompt = (
            f"Generate documentation for this API endpoint:\n\n"
            f"{endpoint_info}\n\n"
            f"Provide:\n"
            f"1. A clear description of what this endpoint does\n"
            f"2. A runnable usage example (curl command)\n"
            f"3. Error code explanations for each response status code"
        )

        result = generate_structured(
            client=self.client,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=EndpointDocumentation,
        )

        doc = GeneratedDoc(
            endpoint_id=endpoint.id,
            version_id=endpoint.version_id,
            description=result.description,
            usage_example=result.usage_example,
            error_codes=result.error_codes,
        )

        return self.doc_repository.create(doc)

    def _build_endpoint_context(self, endpoint: Endpoint) -> str:
        lines = [
            f"Method: {endpoint.method}",
            f"Path: {endpoint.path}",
        ]

        if endpoint.summary:
            lines.append(f"Summary: {endpoint.summary}")

        if endpoint.description:
            lines.append(f"Existing description: {endpoint.description}")

        if endpoint.parameters:
            lines.append(f"Parameters: {json.dumps(endpoint.parameters, indent=2)}")

        if endpoint.request_body:
            lines.append(f"Request body: {json.dumps(endpoint.request_body, indent=2)}")

        if endpoint.responses:
            lines.append(f"Responses: {json.dumps(endpoint.responses, indent=2)}")

        if endpoint.tags:
            lines.append(f"Tags: {', '.join(endpoint.tags)}")

        if endpoint.security:
            lines.append(f"Security: {json.dumps(endpoint.security, indent=2)}")

        return "\n".join(lines)
