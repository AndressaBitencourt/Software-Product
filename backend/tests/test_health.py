from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_modelos_criam_e_consultam(db_session: Session) -> None:
    produto = models.Produto(
        nome="X-Teste", descricao="teste", preco=10, categoria="Teste"
    )
    db_session.add(produto)
    db_session.commit()

    achado = db_session.query(models.Produto).filter_by(nome="X-Teste").one()
    assert achado.id is not None
    assert achado.disponivel is True
