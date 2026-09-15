from sqlmodel import Field, SQLModel


class DocEvaluation(SQLModel, table=True):
    __tablename__ = "doc_evaluations"

    id: int | None = Field(default=None, primary_key=True)

    generated_doc_id: int = Field(foreign_key="generated_docs.id")

    accuracy: float
    completeness: float
    clarity: float

    feedback: str | None = None
