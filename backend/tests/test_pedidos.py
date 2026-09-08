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


def test_listar_pedidos(client: TestClient) -> None:
    client.post("/api/pedidos", json=PEDIDO_VALIDO)
    client.post(
        "/api/pedidos",
        json={"cliente_nome": "João", "itens": [{"produto_id": 2, "quantidade": 1}]},
    )

    resp = client.get("/api/pedidos")
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 2
    primeiro = corpo[0]
    assert set(primeiro) == {
        "id", "cliente_nome", "status", "quantidade_itens", "total", "criado_em"
    }
    # o mais recente (João) vem primeiro
    assert primeiro["cliente_nome"] == "João"
    assert primeiro["quantidade_itens"] == 1
    assert primeiro["total"] == "22.00"


def test_detalhar_pedido(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()

    resp = client.get(f"/api/pedidos/{criado['id']}")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["id"] == criado["id"]
    assert corpo["total"] == "48.00"
    assert len(corpo["itens"]) == 2


def test_detalhar_pedido_inexistente_404(client: TestClient) -> None:
    resp = client.get("/api/pedidos/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Pedido não encontrado."


def test_editar_pedido_recalcula_total(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()

    novo_corpo = {
        "cliente_nome": "Maria Clara",
        "observacao": None,
        "itens": [{"produto_id": 3, "quantidade": 2}],  # X-Tudo 28.00
    }
    resp = client.put(f"/api/pedidos/{criado['id']}", json=novo_corpo)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["cliente_nome"] == "Maria Clara"
    assert len(corpo["itens"]) == 1
    assert corpo["total"] == "56.00"
    assert corpo["atualizado_em"] >= corpo["criado_em"]


def test_editar_pedido_inexistente_404(client: TestClient) -> None:
    resp = client.put(
        "/api/pedidos/999",
        json={"cliente_nome": "X", "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp.status_code == 404


def test_editar_pedido_sem_itens_400(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()
    resp = client.put(
        f"/api/pedidos/{criado['id']}",
        json={"cliente_nome": "Maria", "itens": []},
    )
    assert resp.status_code == 400
