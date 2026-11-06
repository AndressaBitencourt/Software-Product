from collections.abc import Iterator

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
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
    from app.seed import seed_cardapio, seed_usuarios

    seed_cardapio(db_session)
    seed_usuarios(db_session)

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_admin(client: TestClient) -> TestClient:
    from app.seed import ADMIN_PADRAO_EMAIL, ADMIN_PADRAO_SENHA

    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    assert resp.status_code == 200
    return client


@pytest.fixture
def client_atendente(client: TestClient, db_session: Session) -> TestClient:
    senha_hash = bcrypt.hashpw(b"teste123", bcrypt.gensalt()).decode()
    usuario = models.Usuario(
        nome="Atendente Teste",
        email="atendente@teste.com",
        senha_hash=senha_hash,
        papel="atendente",
    )
    db_session.add(usuario)
    db_session.commit()

    resp = client.post(
        "/api/login", json={"email": "atendente@teste.com", "senha": "teste123"}
    )
    assert resp.status_code == 200
    return client
