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


def test_foto_do_seed_e_servida(client: TestClient) -> None:
    resp = client.get("/images/seed/x-salada.jpg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"


def test_placeholder_de_imagem_e_servido(client: TestClient) -> None:
    resp = client.get("/images/seed/placeholder.svg")
    assert resp.status_code == 200
    assert "<svg" in resp.text


def test_cardapio_admin_tem_campo_de_imagem(client: TestClient) -> None:
    resp = client.get("/cardapio-admin.html")
    assert 'id="imagem"' in resp.text
    assert 'id="preview-imagem"' in resp.text


def test_cardapio_admin_tem_campos_de_promocao(client: TestClient) -> None:
    resp = client.get("/cardapio-admin.html")
    assert 'id="em_promocao"' in resp.text
    assert 'id="preco_promocional"' in resp.text


def test_index_tem_carrossel_de_ofertas(client: TestClient) -> None:
    resp = client.get("/")
    assert 'id="carrossel-ofertas"' in resp.text


def test_login_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/login.html")
    assert resp.status_code == 200
    assert "Entrar" in resp.text
    assert "login.js" in resp.text


def test_relatorios_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/relatorios.html")
    assert resp.status_code == 200
    assert "Relatórios" in resp.text
    assert "relatorios.js" in resp.text


def test_carrinho_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/carrinho.html")
    assert resp.status_code == 200
    assert "Carrinho" in resp.text
    assert "carrinho.js" in resp.text


def test_painel_pedidos_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/painel-pedidos.html")
    assert resp.status_code == 200
    assert "Painel de Pedidos" in resp.text
    assert "painel-pedidos.js" in resp.text
