from pydantic import BaseModel


class EndpointDocumentation(BaseModel):
    """LLM structured output schema — the model must return JSON matching this."""

    description: str
    usage_example: str
    error_codes: dict[str, str]


class GeneratedDocResponse(BaseModel):
    id: int
    endpoint_id: int
    version_id: int
    description: str | None = None
    usage_example: str | None = None
    error_codes: dict[str, str] | None = None


class DocEvaluationOutput(BaseModel):
    """LLM-as-a-Judge structured output schema."""

    accuracy: float
    completeness: float
    clarity: float
    feedback: str


class DocEvaluationResponse(BaseModel):
    id: int
    generated_doc_id: int
    accuracy: float
    completeness: float
    clarity: float
    feedback: str | None = None
