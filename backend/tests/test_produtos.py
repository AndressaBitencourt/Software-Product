from sqlalchemy.orm import Session

from app import models
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
