from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.models import utcnow


class RegraNegocioError(Exception):
    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


def listar_produtos(
    db: Session, incluir_indisponiveis: bool = False
) -> list[models.Produto]:
    stmt = select(models.Produto).order_by(
        models.Produto.categoria, models.Produto.nome
    )
    if not incluir_indisponiveis:
        stmt = stmt.where(models.Produto.disponivel.is_(True))
    return list(db.scalars(stmt))


def obter_produto(db: Session, produto_id: int) -> models.Produto | None:
    return db.get(models.Produto, produto_id)


def _montar_itens(
    db: Session, itens_in: list[schemas.ItemPedidoIn]
) -> list[models.ItemPedido]:
    if not itens_in:
        raise RegraNegocioError("O pedido precisa ter pelo menos um item.")
    itens: list[models.ItemPedido] = []
    for entrada in itens_in:
        produto = db.get(models.Produto, entrada.produto_id)
        if produto is None:
            raise RegraNegocioError(
                f"Produto {entrada.produto_id} não existe."
            )
        if not produto.disponivel:
            raise RegraNegocioError(
                f"Produto '{produto.nome}' está indisponível."
            )
        itens.append(
            models.ItemPedido(
                produto_id=produto.id,
                quantidade=entrada.quantidade,
                preco_unitario=produto.preco,
            )
        )
    return itens


def criar_pedido(db: Session, dados: schemas.PedidoIn) -> models.Pedido:
    pedido = models.Pedido(
        cliente_nome=dados.cliente_nome,
        observacao=dados.observacao,
        itens=_montar_itens(db, dados.itens),
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


def listar_pedidos(db: Session) -> list[models.Pedido]:
    stmt = select(models.Pedido).order_by(
        models.Pedido.criado_em.desc(), models.Pedido.id.desc()
    )
    return list(db.scalars(stmt))


def obter_pedido(db: Session, pedido_id: int) -> models.Pedido | None:
    return db.get(models.Pedido, pedido_id)


def atualizar_pedido(
    db: Session, pedido_id: int, dados: schemas.PedidoIn
) -> models.Pedido | None:
    pedido = db.get(models.Pedido, pedido_id)
    if pedido is None:
        return None
    novos_itens = _montar_itens(db, dados.itens)
    pedido.cliente_nome = dados.cliente_nome
    pedido.observacao = dados.observacao
    pedido.itens = novos_itens
    pedido.atualizado_em = utcnow()
    db.commit()
    db.refresh(pedido)
    return pedido


def excluir_pedido(db: Session, pedido_id: int) -> bool:
    pedido = db.get(models.Pedido, pedido_id)
    if pedido is None:
        return False
    db.delete(pedido)
    db.commit()
    return True
