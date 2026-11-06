from fastapi.testclient import TestClient

from app.seed import ADMIN_PADRAO_EMAIL, ADMIN_PADRAO_SENHA


def test_login_valido(client: TestClient) -> None:
    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["email"] == ADMIN_PADRAO_EMAIL
    assert corpo["papel"] == "admin"
    assert "sessao_token" in resp.cookies


def test_login_senha_errada_401(client: TestClient) -> None:
    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": "senha-errada"},
    )
    assert resp.status_code == 401


def test_login_email_inexistente_401(client: TestClient) -> None:
    resp = client.post(
        "/api/login", json={"email": "ninguem@teste.com", "senha": "qualquer"}
    )
    assert resp.status_code == 401


def test_me_sem_sessao_401(client: TestClient) -> None:
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_me_com_sessao_retorna_usuario(client: TestClient) -> None:
    client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    resp = client.get("/api/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == ADMIN_PADRAO_EMAIL


def test_logout_limpa_sessao(client: TestClient) -> None:
    client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    resp = client.post("/api/logout")
    assert resp.status_code == 204
    resp2 = client.get("/api/me")
    assert resp2.status_code == 401
