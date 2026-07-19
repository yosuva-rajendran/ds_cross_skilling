from pydantic import BaseModel


class QueryRequest(BaseModel):
    collection_name: str
    query: str
    top_k: int = 5
    generate_answer: bool = False


class QueryResult(BaseModel):
    text: str
    score: float
    filename: str
    chunk_index: int
    document_id: str


class QueryResponse(BaseModel):
    query: str
    results: list[QueryResult]
    answer: str | None = None
