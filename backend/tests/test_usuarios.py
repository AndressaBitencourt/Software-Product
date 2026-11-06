from sqlalchemy.orm import Session

from app import models
from app.seed import ADMIN_PADRAO_EMAIL, ADMIN_PADRAO_SENHA, seed_usuarios


def test_seed_usuarios_cria_admin_padrao(db_session: Session) -> None:
    inseridos = seed_usuarios(db_session)
    assert inseridos == 1
    admin = db_session.query(models.Usuario).one()
    assert admin.email == ADMIN_PADRAO_EMAIL
    assert admin.papel == "admin"
    assert admin.senha_hash != ADMIN_PADRAO_SENHA  # nunca texto puro


def test_seed_usuarios_e_idempotente(db_session: Session) -> None:
    assert seed_usuarios(db_session) == 1
    assert seed_usuarios(db_session) == 0
    assert db_session.query(models.Usuario).count() == 1
