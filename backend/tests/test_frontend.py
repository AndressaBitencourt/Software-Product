from fastapi.testclient import TestClient


def test_raiz_serve_o_index(client: TestClient) -> None:
    # a fixture `client` já monta o front (create_app monta frontend/ se a pasta existe)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Hamburgueria" in resp.text
    assert "app.js" in resp.text


def test_cardapio_admin_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/cardapio-admin.html")
    assert resp.status_code == 200
    assert "Cardápio" in resp.text
    assert "admin.js" in resp.text


def test_ilustracao_do_seed_e_servida(client: TestClient) -> None:
    resp = client.get("/images/seed/x-salada.svg")
    assert resp.status_code == 200
    assert "<svg" in resp.text


def test_placeholder_de_imagem_e_servido(client: TestClient) -> None:
    resp = client.get("/images/seed/placeholder.svg")
    assert resp.status_code == 200
    assert "<svg" in resp.text
