import json

from openai import OpenAI
from sqlmodel import Session

from app.models.endpoint import Endpoint
from app.models.generated_doc import GeneratedDoc
from app.models.doc_evaluation import DocEvaluation
from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.generated_doc_repository import GeneratedDocRepository
from app.schemas.generated_doc import DocEvaluationOutput
from app.services.llm_client import get_llm_client, generate_structured


JUDGE_SYSTEM_PROMPT = (
    "You are an API documentation quality judge. "
    "Given the original endpoint specification and the generated documentation, "
    "evaluate the documentation quality.\n\n"
    "Score each dimension from 0.0 to 1.0:\n"
    "- accuracy: Does the documentation correctly describe the endpoint?\n"
    "- completeness: Does it cover all parameters, request body, and responses?\n"
    "- clarity: Is it clear and easy for a developer to understand?\n\n"
    "Provide brief feedback explaining your scores."
)


class DocEvaluationService:

    def __init__(self, session: Session, client: OpenAI | None = None):
        self.endpoint_repository = EndpointRepository(session)
        self.doc_repository = GeneratedDocRepository(session)
        self.client = client or get_llm_client()

    def evaluate_version(self, version_id: int) -> list[DocEvaluation]:
        docs = self.doc_repository.get_by_version(version_id)
        endpoints = self.endpoint_repository.get_by_version(version_id)
        endpoint_map = {e.id: e for e in endpoints}
        evaluations = []

        for doc in docs:
            endpoint = endpoint_map.get(doc.endpoint_id)
            if endpoint:
                evaluation = self._evaluate_doc(endpoint, doc)
                evaluations.append(evaluation)

        return evaluations

    def _evaluate_doc(self, endpoint: Endpoint, doc: GeneratedDoc) -> DocEvaluation:

        existing = self.doc_repository.get_evaluation_by_doc(doc.id)
        if existing:
            return existing

        endpoint_info = self._build_context(endpoint)
        doc_info = self._build_doc_text(doc)

        user_prompt = (
            f"## Original Endpoint Specification\n\n"
            f"{endpoint_info}\n\n"
            f"## Generated Documentation\n\n"
            f"{doc_info}\n\n"
            f"Evaluate the quality of this generated documentation."
        )

        result = generate_structured(
            client=self.client,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DocEvaluationOutput,
        )

        evaluation = DocEvaluation(
            generated_doc_id=doc.id,
            accuracy=result.accuracy,
            completeness=result.completeness,
            clarity=result.clarity,
            feedback=result.feedback,
        )

        return self.doc_repository.create_evaluation(evaluation)

    def _build_context(self, endpoint: Endpoint) -> str:
        lines = [
            f"Method: {endpoint.method}",
            f"Path: {endpoint.path}",
        ]
        if endpoint.summary:
            lines.append(f"Summary: {endpoint.summary}")
        if endpoint.parameters:
            lines.append(f"Parameters: {json.dumps(endpoint.parameters, indent=2)}")
        if endpoint.request_body:
            lines.append(f"Request body: {json.dumps(endpoint.request_body, indent=2)}")
        if endpoint.responses:
            lines.append(f"Responses: {json.dumps(endpoint.responses, indent=2)}")
        return "\n".join(lines)

    def _build_doc_text(self, doc: GeneratedDoc) -> str:
        lines = []
        if doc.description:
            lines.append(f"Description: {doc.description}")
        if doc.usage_example:
            lines.append(f"Usage example:\n{doc.usage_example}")
        if doc.error_codes:
            lines.append(f"Error codes: {json.dumps(doc.error_codes, indent=2)}")
        return "\n".join(lines)
