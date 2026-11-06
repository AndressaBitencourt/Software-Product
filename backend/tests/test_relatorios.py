from fastapi.testclient import TestClient

PEDIDO_A = {
    "cliente_nome": "Bruno",
    "itens": [{"produto_id": 1, "quantidade": 2}],  # X-Salada 18.00 x2 = 36.00
}
PEDIDO_B = {
    "cliente_nome": "Carla",
    "itens": [{"produto_id": 5, "quantidade": 3}],  # Batata Frita 12.00 x3 = 36.00
}


def test_relatorios_bloqueado_pra_atendente(client_atendente: TestClient) -> None:
    resp = client_atendente.get("/api/relatorios/resumo")
    assert resp.status_code == 403


def test_resumo_relatorio(client_admin: TestClient) -> None:
    client_admin.post("/api/pedidos", json=PEDIDO_A)
    client_admin.post("/api/pedidos", json=PEDIDO_B)

    resp = client_admin.get("/api/relatorios/resumo")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["total_pedidos"] == 2
    assert corpo["faturamento_total"] == "72.00"
    assert corpo["ticket_medio"] == "36.00"


def test_resumo_relatorio_sem_pedidos(client_admin: TestClient) -> None:
    resp = client_admin.get("/api/relatorios/resumo")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["total_pedidos"] == 0
    assert corpo["ticket_medio"] == "0.00"


def test_produtos_mais_vendidos(client_admin: TestClient) -> None:
    client_admin.post("/api/pedidos", json=PEDIDO_A)
    resp = client_admin.get("/api/relatorios/produtos-mais-vendidos")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo[0]["produto_nome"] == "X-Salada"
    assert corpo[0]["quantidade_total"] == 2


def test_faturamento_diario(client_admin: TestClient) -> None:
    client_admin.post("/api/pedidos", json=PEDIDO_A)
    resp = client_admin.get("/api/relatorios/faturamento-diario")
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 1
    assert corpo[0]["total"] == "36.00"


def test_buscar_pedidos_por_cliente(client_atendente: TestClient) -> None:
    client_atendente.post("/api/pedidos", json=PEDIDO_A)
    client_atendente.post("/api/pedidos", json=PEDIDO_B)

    resp = client_atendente.get("/api/pedidos", params={"cliente_nome": "bru"})
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 1
    assert corpo[0]["cliente_nome"] == "Bruno"
