from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models

CARDAPIO_INICIAL: list[dict] = [
    {"nome": "X-Salada", "descricao": "Hambúrguer, queijo, alface, tomate e maionese",
     "preco": Decimal("18.00"), "categoria": "Clássicos",
     "imagem_url": "/images/seed/x-salada.jpg"},
    {"nome": "X-Bacon", "descricao": "Hambúrguer, queijo, bacon crocante e maionese",
     "preco": Decimal("22.00"), "categoria": "Clássicos",
     "imagem_url": "/images/seed/x-bacon.jpg"},
    {"nome": "X-Tudo", "descricao": "Dois hambúrgueres, queijo, bacon, ovo, salada e batata palha",
     "preco": Decimal("28.00"), "categoria": "Especiais",
     "imagem_url": "/images/seed/x-tudo.jpg",
     "em_promocao": True, "preco_promocional": Decimal("22.90")},
    {"nome": "X-Vegetariano", "descricao": "Hambúrguer de grão-de-bico, queijo, rúcula e tomate seco",
     "preco": Decimal("24.00"), "categoria": "Especiais",
     "imagem_url": "/images/seed/x-vegetariano.jpg"},
    {"nome": "Batata Frita", "descricao": "Porção individual de batata frita",
     "preco": Decimal("12.00"), "categoria": "Acompanhamentos",
     "imagem_url": "/images/seed/batata-frita.jpg"},
    {"nome": "Onion Rings", "descricao": "Anéis de cebola empanados",
     "preco": Decimal("14.00"), "categoria": "Acompanhamentos",
     "imagem_url": "/images/seed/onion-rings.jpg"},
    {"nome": "Coca-Cola Cherry Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/coca-cola-cherry.jpg",
     "em_promocao": True, "preco_promocional": Decimal("4.50")},
    {"nome": "Coca-Cola Zero Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/coca-cola-zero.jpg"},
    {"nome": "Guaraná Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/guarana.jpg"},
    {"nome": "Fanta Laranja Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/fanta-laranja.jpg"},
    {"nome": "Sprite Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/sprite.jpg"},
    {"nome": "Suco Natural", "descricao": "Copo 300 ml, sabores do dia",
     "preco": Decimal("9.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/suco.jpg"},
    {"nome": "Sundae de Chocolate", "descricao": "Sorvete, calda de chocolate e wafer",
     "preco": Decimal("10.00"), "categoria": "Sobremesas",
     "imagem_url": "/images/seed/sundae-chocolate.jpg"},
    {"nome": "Torta de Limão", "descricao": "Fatia de torta de limão com merengue",
     "preco": Decimal("12.00"), "categoria": "Sobremesas",
     "imagem_url": "/images/seed/torta-limao.jpg"},
    {"nome": "Petit Gâteau", "descricao": "Bolo de chocolate quente com sorvete de creme",
     "preco": Decimal("16.00"), "categoria": "Sobremesas",
     "imagem_url": "/images/seed/petit-gateau.jpg",
     "em_promocao": True, "preco_promocional": Decimal("12.90")},
    {"nome": "Casquinha de Baunilha", "descricao": "Sorvete soft de baunilha",
     "preco": Decimal("7.00"), "categoria": "Sobremesas",
     "imagem_url": "/images/seed/casquinha-baunilha.jpg"},
    {"nome": "Brownie com Sorvete", "descricao": "Brownie quente, sorvete de creme e calda de chocolate",
     "preco": Decimal("14.00"), "categoria": "Sobremesas",
     "imagem_url": "/images/seed/brownie-sorvete.jpg"},
]


def seed_cardapio(db: Session) -> int:
    ja_existem = db.scalar(select(func.count()).select_from(models.Produto))
    if ja_existem:
        return 0
    db.add_all(models.Produto(**item) for item in CARDAPIO_INICIAL)
    db.commit()
    return len(CARDAPIO_INICIAL)
