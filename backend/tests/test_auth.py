from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import auth, models
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


def test_me_com_sessao_expirada_401(client: TestClient, db_session: Session) -> None:
    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    usuario_id = resp.json()["id"]

    # `criar_sessao` sempre gera expira_em no futuro, então para testar o
    # caminho de sessão expirada inserimos a linha diretamente no banco,
    # com expira_em no passado.
    token_expirado = "e" * 64
    agora = datetime.now(timezone.utc)
    db_session.add(
        models.Sessao(
            token=token_expirado,
            usuario_id=usuario_id,
            criado_em=agora - timedelta(hours=10),
            expira_em=agora - timedelta(hours=2),
        )
    )
    db_session.commit()

    client.cookies.set(auth.NOME_COOKIE, token_expirado)
    resp2 = client.get("/api/me")
    assert resp2.status_code == 401
