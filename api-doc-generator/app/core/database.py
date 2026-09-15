from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.models import Project, Endpoint, ComponentSchema, APIVersion, GeneratedDoc, DocEvaluation


engine = create_engine(
    settings.database_url,
    echo=settings.debug,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session