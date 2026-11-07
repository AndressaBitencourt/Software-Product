from sqlalchemy.orm import Session

from app import models
from app.seed import (
    ADMIN_PADRAO_EMAIL,
    ADMIN_PADRAO_SENHA,
    ATENDENTE_PADRAO_EMAIL,
    ATENDENTE_PADRAO_SENHA,
    seed_usuarios,
)


def test_seed_usuarios_cria_admin_e_atendente_padrao(db_session: Session) -> None:
    inseridos = seed_usuarios(db_session)
    assert inseridos == 2
    admin = db_session.query(models.Usuario).filter_by(email=ADMIN_PADRAO_EMAIL).one()
    assert admin.papel == "admin"
    assert admin.senha_hash != ADMIN_PADRAO_SENHA  # nunca texto puro
    atendente = (
        db_session.query(models.Usuario).filter_by(email=ATENDENTE_PADRAO_EMAIL).one()
    )
    assert atendente.papel == "atendente"
    assert atendente.senha_hash != ATENDENTE_PADRAO_SENHA  # nunca texto puro


def test_seed_usuarios_e_idempotente(db_session: Session) -> None:
    assert seed_usuarios(db_session) == 2
    assert seed_usuarios(db_session) == 0
    assert db_session.query(models.Usuario).count() == 2
