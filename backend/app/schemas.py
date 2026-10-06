from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

Money = Annotated[
    Decimal, PlainSerializer(lambda v: f"{Decimal(v):.2f}", return_type=str)
]


def _utc_iso(v: datetime) -> str:
    aware = (
        v.replace(tzinfo=timezone.utc)
        if v.tzinfo is None
        else v.astimezone(timezone.utc)
    )
    return aware.isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[datetime, PlainSerializer(_utc_iso, return_type=str)]


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None = None
    preco: Money
    categoria: str
    disponivel: bool


class ProdutoIn(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    categoria: str = Field(min_length=1, max_length=40)
    disponivel: bool = True

    @field_validator("nome", "categoria", mode="after")
    @classmethod
    def _remover_espacos(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("não pode ser só espaços.")
        return valor


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
    criado_em: UtcDatetime
    atualizado_em: UtcDatetime
    itens: list[ItemPedidoOut]
    total: Money


class PedidoResumo(BaseModel):
    id: int
    cliente_nome: str
    status: str
    quantidade_itens: int
    total: Money
    criado_em: UtcDatetime
