from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.seed import CARDAPIO_INICIAL, seed_cardapio


def test_seed_popula_oito_itens(db_session: Session) -> None:
    inseridos = seed_cardapio(db_session)
    assert inseridos == 8
    assert db_session.query(models.Produto).count() == 8


def test_seed_e_idempotente(db_session: Session) -> None:
    assert seed_cardapio(db_session) == 8
    assert seed_cardapio(db_session) == 0
    assert db_session.query(models.Produto).count() == 8


def test_cardapio_inicial_tem_quatro_categorias(db_session: Session) -> None:
    categorias = {item["categoria"] for item in CARDAPIO_INICIAL}
    assert categorias == {
        "Clássicos",
        "Especiais",
        "Acompanhamentos",
        "Bebidas",
    }


def test_get_produtos_retorna_seed(client: TestClient) -> None:
    resp = client.get("/api/produtos")
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 8
    primeiro = corpo[0]
    assert set(primeiro) == {
        "id", "nome", "descricao", "preco", "categoria", "disponivel"
    }
    assert isinstance(primeiro["preco"], str)
    assert primeiro["preco"].count(".") == 1


def test_get_produtos_incluir_indisponiveis(client: TestClient, db_session) -> None:
    from app import models

    produto = db_session.get(models.Produto, 1)
    produto.disponivel = False
    db_session.commit()

    padrao = client.get("/api/produtos")
    assert len(padrao.json()) == 7

    completo = client.get("/api/produtos", params={"incluir_indisponiveis": "true"})
    assert len(completo.json()) == 8


def test_get_produto_por_id(client: TestClient) -> None:
    resp = client.get("/api/produtos/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_get_produto_inexistente_404(client: TestClient) -> None:
    resp = client.get("/api/produtos/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Produto não encontrado."
