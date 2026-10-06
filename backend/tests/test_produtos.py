import base64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models, uploads
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
        "id", "nome", "descricao", "preco", "categoria", "disponivel", "imagem_url"
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


PRODUTO_NOVO = {
    "nome": "X-Frango",
    "descricao": "Frango grelhado, queijo, alface e maionese",
    "preco": "21.50",
    "categoria": "Clássicos",
    "disponivel": True,
}


def test_criar_produto_valido(client: TestClient) -> None:
    resp = client.post("/api/produtos", json=PRODUTO_NOVO)
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["nome"] == "X-Frango"
    assert corpo["preco"] == "21.50"
    assert corpo["disponivel"] is True

    listados = client.get("/api/produtos").json()
    assert len(listados) == 9


def test_criar_produto_nome_duplicado_400(client: TestClient) -> None:
    resp = client.post(
        "/api/produtos",
        json={**PRODUTO_NOVO, "nome": "X-Salada"},
    )
    assert resp.status_code == 400
    assert "X-Salada" in resp.json()["detail"]


def test_criar_produto_preco_invalido_422(client: TestClient) -> None:
    resp = client.post("/api/produtos", json={**PRODUTO_NOVO, "preco": "0"})
    assert resp.status_code == 422


def test_editar_produto(client: TestClient) -> None:
    resp = client.put(
        "/api/produtos/1",
        json={
            "nome": "X-Salada Supreme",
            "descricao": "Hambúrguer duplo, queijo, alface, tomate e maionese",
            "preco": "20.00",
            "categoria": "Clássicos",
            "disponivel": False,
        },
    )
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["nome"] == "X-Salada Supreme"
    assert corpo["preco"] == "20.00"
    assert corpo["disponivel"] is False


def test_editar_produto_nome_de_outro_400(client: TestClient) -> None:
    resp = client.put(
        "/api/produtos/1",
        json={**PRODUTO_NOVO, "nome": "X-Bacon"},
    )
    assert resp.status_code == 400
    assert "X-Bacon" in resp.json()["detail"]


def test_editar_produto_inexistente_404(client: TestClient) -> None:
    resp = client.put("/api/produtos/999", json=PRODUTO_NOVO)
    assert resp.status_code == 404


def test_excluir_produto_sem_pedido(client: TestClient) -> None:
    criado = client.post("/api/produtos", json=PRODUTO_NOVO).json()

    resp = client.delete(f"/api/produtos/{criado['id']}")
    assert resp.status_code == 204

    assert client.get(f"/api/produtos/{criado['id']}").status_code == 404


def test_excluir_produto_com_pedido_400(client: TestClient) -> None:
    resp_pedido = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp_pedido.status_code == 201

    resp = client.delete("/api/produtos/1")
    assert resp.status_code == 400
    assert "pedidos" in resp.json()["detail"]
    assert client.get("/api/produtos/1").status_code == 200


def test_excluir_produto_inexistente_404(client: TestClient) -> None:
    resp = client.delete("/api/produtos/999")
    assert resp.status_code == 404


def test_editar_produto_mantendo_proprio_nome(client: TestClient) -> None:
    atual = client.get("/api/produtos/1").json()
    resp = client.put(
        "/api/produtos/1",
        json={
            "nome": atual["nome"],
            "descricao": atual["descricao"],
            "preco": atual["preco"],
            "categoria": atual["categoria"],
            "disponivel": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["disponivel"] is False
    assert len(client.get("/api/produtos").json()) == 7


_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def uploads_tmp(tmp_path, monkeypatch):
    produtos_dir = tmp_path / "produtos"
    produtos_dir.mkdir()
    monkeypatch.setattr(uploads, "UPLOADS_ROOT", tmp_path)
    monkeypatch.setattr(uploads, "PRODUTOS_DIR", produtos_dir)
    return produtos_dir


def test_upload_imagem_produto(client: TestClient, uploads_tmp) -> None:
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["imagem_url"].startswith("/uploads/produtos/1-")
    assert len(list(uploads_tmp.iterdir())) == 1


def test_upload_imagem_substitui_anterior(client: TestClient, uploads_tmp) -> None:
    client.post("/api/produtos/1/imagem", files={"arquivo": ("a.png", _PNG_1X1, "image/png")})
    client.post("/api/produtos/1/imagem", files={"arquivo": ("b.png", _PNG_1X1, "image/png")})
    assert len(list(uploads_tmp.iterdir())) == 1


def test_upload_imagem_formato_invalido_400(client: TestClient, uploads_tmp) -> None:
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("doc.txt", b"nao e imagem", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_imagem_produto_inexistente_404(client: TestClient, uploads_tmp) -> None:
    resp = client.post(
        "/api/produtos/999/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 404


def test_upload_imagem_muito_grande_400(client: TestClient, uploads_tmp) -> None:
    conteudo_grande = b"0" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("foto.png", conteudo_grande, "image/png")},
    )
    assert resp.status_code == 400


def test_excluir_produto_remove_arquivo_de_imagem(client: TestClient, uploads_tmp) -> None:
    criado = client.post("/api/produtos", json=PRODUTO_NOVO).json()
    client.post(
        f"/api/produtos/{criado['id']}/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert len(list(uploads_tmp.iterdir())) == 1

    client.delete(f"/api/produtos/{criado['id']}")
    assert len(list(uploads_tmp.iterdir())) == 0


def test_seed_grava_imagem_de_cada_item(db_session: Session) -> None:
    seed_cardapio(db_session)
    produtos = db_session.query(models.Produto).all()
    assert all(p.imagem_url is not None for p in produtos)
    assert all(p.imagem_url.startswith("/images/seed/") for p in produtos)


def test_mount_uploads_serve_arquivo_real(uploads_tmp, client: TestClient) -> None:
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 200
    imagem_url = resp.json()["imagem_url"]
    baixado = client.get(imagem_url)
    assert baixado.status_code == 200
    assert baixado.content == _PNG_1X1
