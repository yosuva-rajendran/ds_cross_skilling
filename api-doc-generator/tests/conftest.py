import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models import Project, Endpoint, ComponentSchema, APIVersion


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project(session: Session) -> Project:
    project = Project(name="Test Project", repository_url="https://github.com/test/repo")
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@pytest.fixture
def sample_versions(session: Session, sample_project: Project) -> tuple[APIVersion, APIVersion]:
    v1 = APIVersion(project_id=sample_project.id, version="1.0.0")
    v2 = APIVersion(project_id=sample_project.id, version="1.1.0")
    session.add(v1)
    session.add(v2)
    session.commit()
    session.refresh(v1)
    session.refresh(v2)
    return v1, v2
