from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models

CARDAPIO_INICIAL: list[dict] = [
    {"nome": "X-Salada", "descricao": "Hambúrguer, queijo, alface, tomate e maionese",
     "preco": Decimal("18.00"), "categoria": "Clássicos"},
    {"nome": "X-Bacon", "descricao": "Hambúrguer, queijo, bacon crocante e maionese",
     "preco": Decimal("22.00"), "categoria": "Clássicos"},
    {"nome": "X-Tudo", "descricao": "Dois hambúrgueres, queijo, bacon, ovo, salada e batata palha",
     "preco": Decimal("28.00"), "categoria": "Especiais"},
    {"nome": "X-Vegetariano", "descricao": "Hambúrguer de grão-de-bico, queijo, rúcula e tomate seco",
     "preco": Decimal("24.00"), "categoria": "Especiais"},
    {"nome": "Batata Frita", "descricao": "Porção individual de batata frita",
     "preco": Decimal("12.00"), "categoria": "Acompanhamentos"},
    {"nome": "Onion Rings", "descricao": "Anéis de cebola empanados",
     "preco": Decimal("14.00"), "categoria": "Acompanhamentos"},
    {"nome": "Refrigerante Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas"},
    {"nome": "Suco Natural", "descricao": "Copo 300 ml, sabores do dia",
     "preco": Decimal("9.00"), "categoria": "Bebidas"},
]


def seed_cardapio(db: Session) -> int:
    ja_existem = db.scalar(select(func.count()).select_from(models.Produto))
    if ja_existem:
        return 0
    db.add_all(models.Produto(**item) for item in CARDAPIO_INICIAL)
    db.commit()
    return len(CARDAPIO_INICIAL)
