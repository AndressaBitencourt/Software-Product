from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

Money = Annotated[
    Decimal, PlainSerializer(lambda v: f"{Decimal(v):.2f}", return_type=str)
]


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None = None
    preco: Money
    categoria: str
    disponivel: bool


class ItemPedidoIn(BaseModel):
    produto_id: int
    quantidade: int = Field(ge=1)


class PedidoIn(BaseModel):
    cliente_nome: str = Field(min_length=1, max_length=80)
    observacao: str | None = Field(default=None, max_length=255)
    itens: list[ItemPedidoIn]


class ItemPedidoOut(BaseModel):
    id: int
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: Money
    subtotal: Money


class PedidoOut(BaseModel):
    id: int
    cliente_nome: str
    observacao: str | None
    status: str
    criado_em: datetime
    atualizado_em: datetime
    itens: list[ItemPedidoOut]
    total: Money


class PedidoResumo(BaseModel):
    id: int
    cliente_nome: str
    status: str
    quantidade_itens: int
    total: Money
    criado_em: datetime
