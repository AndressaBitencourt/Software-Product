from fastapi.testclient import TestClient

PEDIDO_VALIDO = {
    "cliente_nome": "Maria",
    "observacao": "sem cebola",
    "itens": [
        {"produto_id": 1, "quantidade": 2},  # X-Salada 18.00
        {"produto_id": 5, "quantidade": 1},  # Batata Frita 12.00
    ],
}


def test_criar_pedido_valido(client: TestClient) -> None:
    resp = client.post("/api/pedidos", json=PEDIDO_VALIDO)
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["cliente_nome"] == "Maria"
    assert corpo["status"] == "recebido"
    assert corpo["total"] == "48.00"
    assert len(corpo["itens"]) == 2
    item = corpo["itens"][0]
    assert item["produto_nome"] == "X-Salada"
    assert item["preco_unitario"] == "18.00"
    assert item["subtotal"] == "36.00"


def test_criar_pedido_sem_itens_400(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos", json={"cliente_nome": "Ana", "itens": []}
    )
    assert resp.status_code == 400
    assert "pelo menos um item" in resp.json()["detail"]


def test_criar_pedido_produto_inexistente_400(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 999, "quantidade": 1}]},
    )
    assert resp.status_code == 400
    assert "999" in resp.json()["detail"]


def test_criar_pedido_quantidade_zero_422(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 1, "quantidade": 0}]},
    )
    assert resp.status_code == 422


def test_criar_pedido_sem_cliente_422(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos",
        json={"itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp.status_code == 422


def test_criar_pedido_produto_indisponivel_400(client: TestClient, db_session) -> None:
    from app import models

    db_session.get(models.Produto, 1).disponivel = False
    db_session.commit()

    resp = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp.status_code == 400
    assert "indisponível" in resp.json()["detail"]
