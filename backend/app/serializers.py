from decimal import Decimal

from app import models, schemas


def _subtotal(item: models.ItemPedido) -> Decimal:
    return Decimal(item.preco_unitario) * item.quantidade


def pedido_para_out(pedido: models.Pedido) -> schemas.PedidoOut:
    itens = [
        schemas.ItemPedidoOut(
            id=item.id,
            produto_id=item.produto_id,
            produto_nome=item.produto.nome,
            quantidade=item.quantidade,
            preco_unitario=Decimal(item.preco_unitario),
            subtotal=_subtotal(item),
        )
        for item in pedido.itens
    ]
    total = sum((_subtotal(i) for i in pedido.itens), Decimal("0"))
    return schemas.PedidoOut(
        id=pedido.id,
        cliente_nome=pedido.cliente_nome,
        observacao=pedido.observacao,
        status=pedido.status,
        criado_em=pedido.criado_em,
        atualizado_em=pedido.atualizado_em,
        itens=itens,
        total=total,
    )


def pedido_para_resumo(pedido: models.Pedido) -> schemas.PedidoResumo:
    total = sum((_subtotal(i) for i in pedido.itens), Decimal("0"))
    return schemas.PedidoResumo(
        id=pedido.id,
        cliente_nome=pedido.cliente_nome,
        status=pedido.status,
        quantidade_itens=sum(i.quantidade for i in pedido.itens),
        total=total,
        criado_em=pedido.criado_em,
    )
