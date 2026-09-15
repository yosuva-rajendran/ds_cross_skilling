from sqlmodel import Session, select

from app.models.generated_doc import GeneratedDoc
from app.models.doc_evaluation import DocEvaluation


class GeneratedDocRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, doc: GeneratedDoc) -> GeneratedDoc:
        self.session.add(doc)
        self.session.commit()
        self.session.refresh(doc)
        return doc

    def get_by_version(self, version_id: int) -> list[GeneratedDoc]:
        statement = select(GeneratedDoc).where(
            GeneratedDoc.version_id == version_id
        )
        return list(self.session.exec(statement).all())

    def get_by_endpoint(self, endpoint_id: int) -> GeneratedDoc | None:
        statement = select(GeneratedDoc).where(
            GeneratedDoc.endpoint_id == endpoint_id
        )
        return self.session.exec(statement).first()

    def create_evaluation(self, evaluation: DocEvaluation) -> DocEvaluation:
        self.session.add(evaluation)
        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation

    def get_evaluation_by_doc(self, generated_doc_id: int) -> DocEvaluation | None:
        statement = select(DocEvaluation).where(
            DocEvaluation.generated_doc_id == generated_doc_id
        )
        return self.session.exec(statement).first()
