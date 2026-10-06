from sqlalchemy import func, select
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


def _nome_de_produto_em_uso(
    db: Session, nome: str, ignorar_id: int | None = None
) -> bool:
    stmt = select(models.Produto).where(models.Produto.nome == nome)
    if ignorar_id is not None:
        stmt = stmt.where(models.Produto.id != ignorar_id)
    return db.scalar(stmt) is not None


def criar_produto(db: Session, dados: schemas.ProdutoIn) -> models.Produto:
    if _nome_de_produto_em_uso(db, dados.nome):
        raise RegraNegocioError(f"Já existe um produto chamado '{dados.nome}'.")
    produto = models.Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        categoria=dados.categoria,
        disponivel=dados.disponivel,
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def atualizar_produto(
    db: Session, produto_id: int, dados: schemas.ProdutoIn
) -> models.Produto | None:
    produto = db.get(models.Produto, produto_id)
    if produto is None:
        return None
    if _nome_de_produto_em_uso(db, dados.nome, ignorar_id=produto_id):
        raise RegraNegocioError(f"Já existe um produto chamado '{dados.nome}'.")
    produto.nome = dados.nome
    produto.descricao = dados.descricao
    produto.preco = dados.preco
    produto.categoria = dados.categoria
    produto.disponivel = dados.disponivel
    db.commit()
    db.refresh(produto)
    return produto


def _montar_itens(
    db: Session,
    itens_in: list[schemas.ItemPedidoIn],
    produtos_ja_aceitos: frozenset[int] = frozenset(),
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
        if not produto.disponivel and produto.id not in produtos_ja_aceitos:
            raise RegraNegocioError(
                f"Produto '{produto.nome}' está indisponível."
            )
        itens.append(
            models.ItemPedido(
                produto_id=produto.id,
                produto_nome=produto.nome,
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
    produtos_ja_aceitos = frozenset(item.produto_id for item in pedido.itens)
    novos_itens = _montar_itens(db, dados.itens, produtos_ja_aceitos)
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


def excluir_produto(db: Session, produto_id: int) -> bool:
    produto = db.get(models.Produto, produto_id)
    if produto is None:
        return False
    em_uso = db.scalar(
        select(func.count())
        .select_from(models.ItemPedido)
        .where(models.ItemPedido.produto_id == produto_id)
    )
    if em_uso:
        raise RegraNegocioError(
            "Não é possível excluir — esse produto já aparece em pedidos. "
            "Marque como indisponível em vez de excluir."
        )
    db.delete(produto)
    db.commit()
    return True
