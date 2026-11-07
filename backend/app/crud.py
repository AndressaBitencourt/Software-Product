from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas, uploads
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


def _preco_promocional_valido(dados: schemas.ProdutoIn) -> Decimal | None:
    if not dados.em_promocao:
        return None
    if dados.preco_promocional is None:
        raise RegraNegocioError(
            "Produto em promoção precisa de um preço promocional."
        )
    if dados.preco_promocional >= dados.preco:
        raise RegraNegocioError(
            "O preço promocional precisa ser menor que o preço normal."
        )
    return dados.preco_promocional


def criar_produto(db: Session, dados: schemas.ProdutoIn) -> models.Produto:
    if _nome_de_produto_em_uso(db, dados.nome):
        raise RegraNegocioError(f"Já existe um produto chamado '{dados.nome}'.")
    produto = models.Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        categoria=dados.categoria,
        disponivel=dados.disponivel,
        em_promocao=dados.em_promocao,
        preco_promocional=_preco_promocional_valido(dados),
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
    produto.em_promocao = dados.em_promocao
    produto.preco_promocional = _preco_promocional_valido(dados)
    db.commit()
    db.refresh(produto)
    return produto


async def salvar_imagem_produto(
    db: Session, produto_id: int, arquivo
) -> models.Produto | None:
    produto = db.get(models.Produto, produto_id)
    if produto is None:
        return None
    extensao = uploads.extensao_valida(arquivo.filename or "")
    if extensao is None:
        raise RegraNegocioError(
            "Formato de imagem não suportado. Use JPG, PNG ou WEBP."
        )
    conteudo = await arquivo.read()
    if len(conteudo) > uploads.TAMANHO_MAXIMO_BYTES:
        raise RegraNegocioError("Imagem muito grande — o limite é 5 MB.")
    uploads.remover_arquivo(produto.imagem_url)
    produto.imagem_url = uploads.salvar_arquivo(produto_id, extensao, conteudo)
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


def _normalizar_utc(momento: datetime | None) -> datetime | None:
    """SQLite guarda `criado_em` como texto ingenuo (sempre produzido por
    `utcnow()`, portanto ja em UTC). O bind processor do dialeto sqlite
    formata datetimes usando os campos literais (ano/mes/.../microsegundo)
    e IGNORA o tzinfo -- nao faz `.astimezone(utc)` sozinho. Como esta
    funcao e o unico ponto onde datetimes vindos de fora (query params)
    entram na comparacao com `criado_em`, qualquer datetime com offset
    explicito precisa ser convertido para UTC aqui antes da comparacao --
    senao o filtro desliza pelo valor do offset. Datetime ingenuo (sem
    tzinfo) e deixado como esta, pois ja é assumido UTC."""
    if momento is not None and momento.tzinfo is not None:
        return momento.astimezone(timezone.utc)
    return momento


def listar_pedidos(
    db: Session,
    cliente_nome: str | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> list[models.Pedido]:
    data_inicio = _normalizar_utc(data_inicio)
    data_fim = _normalizar_utc(data_fim)
    stmt = select(models.Pedido).order_by(
        models.Pedido.criado_em.desc(), models.Pedido.id.desc()
    )
    if cliente_nome:
        stmt = stmt.where(models.Pedido.cliente_nome.ilike(f"%{cliente_nome}%"))
    if data_inicio:
        stmt = stmt.where(models.Pedido.criado_em >= data_inicio)
    if data_fim:
        stmt = stmt.where(models.Pedido.criado_em <= data_fim)
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
    uploads.remover_arquivo(produto.imagem_url)
    db.delete(produto)
    db.commit()
    return True


def _item_subtotal(item: models.ItemPedido) -> Decimal:
    return Decimal(item.preco_unitario) * item.quantidade


def resumo_relatorio(
    db: Session, data_inicio: datetime, data_fim: datetime
) -> tuple[int, Decimal, Decimal]:
    pedidos = listar_pedidos(db, data_inicio=data_inicio, data_fim=data_fim)
    total_pedidos = len(pedidos)
    faturamento_total = sum(
        (_item_subtotal(item) for pedido in pedidos for item in pedido.itens),
        Decimal("0"),
    )
    ticket_medio = (
        faturamento_total / total_pedidos if total_pedidos else Decimal("0")
    )
    return total_pedidos, faturamento_total, ticket_medio


def faturamento_diario(
    db: Session, data_inicio: datetime, data_fim: datetime
) -> list[tuple[date, Decimal]]:
    pedidos = listar_pedidos(db, data_inicio=data_inicio, data_fim=data_fim)
    totais_por_dia: dict[date, Decimal] = {}
    for pedido in pedidos:
        dia = pedido.criado_em.date()
        subtotal_pedido = sum(
            (_item_subtotal(item) for item in pedido.itens), Decimal("0")
        )
        totais_por_dia[dia] = totais_por_dia.get(dia, Decimal("0")) + subtotal_pedido
    return sorted(totais_por_dia.items())


def produtos_mais_vendidos(
    db: Session, data_inicio: datetime, data_fim: datetime, limite: int
) -> list[tuple[str, int]]:
    data_inicio = _normalizar_utc(data_inicio)
    data_fim = _normalizar_utc(data_fim)
    stmt = (
        select(
            models.ItemPedido.produto_nome,
            func.sum(models.ItemPedido.quantidade).label("total"),
        )
        .join(models.Pedido, models.Pedido.id == models.ItemPedido.pedido_id)
        .where(models.Pedido.criado_em >= data_inicio)
        .where(models.Pedido.criado_em <= data_fim)
        .group_by(models.ItemPedido.produto_nome)
        .order_by(func.sum(models.ItemPedido.quantidade).desc())
        .limit(limite)
    )
    return list(db.execute(stmt).all())
