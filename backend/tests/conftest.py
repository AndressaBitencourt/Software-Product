from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app


@pytest.fixture
def db_session() -> Iterator[Session]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _fk_on(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(test_engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app(inicializar=False)

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
