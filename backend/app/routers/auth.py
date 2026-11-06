from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api", tags=["autenticacao"])


@router.post("/login", response_model=schemas.UsuarioOut)
def login(
    dados: schemas.LoginIn, response: Response, db: Session = Depends(get_db)
):
    usuario = auth.autenticar(db, dados.email, dados.senha)
    if usuario is None:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    token = auth.criar_sessao(db, usuario.id)
    response.set_cookie(
        key=auth.NOME_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=int(auth.DURACAO_SESSAO.total_seconds()),
    )
    return usuario


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    sessao_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if sessao_token is not None:
        auth.excluir_sessao(db, sessao_token)
    response.delete_cookie(auth.NOME_COOKIE)


@router.get("/me", response_model=schemas.UsuarioOut)
def me(usuario: models.Usuario = Depends(auth.usuario_logado)):
    return usuario
