import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

NOME_COOKIE = "sessao_token"
DURACAO_SESSAO = timedelta(hours=8)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def autenticar(db: Session, email: str, senha: str) -> models.Usuario | None:
    usuario = db.scalar(select(models.Usuario).where(models.Usuario.email == email))
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario


def criar_sessao(db: Session, usuario_id: int) -> str:
    token = secrets.token_hex(32)
    agora = datetime.now(timezone.utc)
    sessao = models.Sessao(
        token=token,
        usuario_id=usuario_id,
        criado_em=agora,
        expira_em=agora + DURACAO_SESSAO,
    )
    db.add(sessao)
    db.commit()
    return token


def excluir_sessao(db: Session, token: str) -> None:
    sessao = db.get(models.Sessao, token)
    if sessao is not None:
        db.delete(sessao)
        db.commit()


def usuario_logado(
    sessao_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """Dependencia FastAPI: qualquer papel logado. O nome do parametro
    `sessao_token` precisa bater com NOME_COOKIE -- e como o FastAPI le
    cookie pelo nome do parametro."""
    if sessao_token is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    sessao = db.get(models.Sessao, sessao_token)
    if sessao is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    expira_em = sessao.expira_em
    if expira_em.tzinfo is None:
        # SQLite não guarda timezone: DateTime(timezone=True) volta "naive".
        expira_em = expira_em.replace(tzinfo=timezone.utc)
    if expira_em < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    usuario = db.get(models.Usuario, sessao.usuario_id)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return usuario


def usuario_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    if usuario.papel != "admin":
        raise HTTPException(
            status_code=403, detail="Acesso restrito a administradores."
        )
    return usuario
