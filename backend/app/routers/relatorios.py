from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import auth, crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


def _periodo_padrao(
    data_inicio: datetime | None, data_fim: datetime | None
) -> tuple[datetime, datetime]:
    fim = data_fim or datetime.now(timezone.utc)
    inicio = data_inicio or fim - timedelta(days=30)
    return inicio, fim


@router.get("/resumo", response_model=schemas.ResumoRelatorio)
def resumo(
    data_inicio: datetime | None = Query(default=None),
    data_fim: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    inicio, fim = _periodo_padrao(data_inicio, data_fim)
    total_pedidos, faturamento_total, ticket_medio = crud.resumo_relatorio(
        db, inicio, fim
    )
    return schemas.ResumoRelatorio(
        total_pedidos=total_pedidos,
        faturamento_total=faturamento_total,
        ticket_medio=ticket_medio,
    )


@router.get(
    "/faturamento-diario", response_model=list[schemas.FaturamentoDiarioItem]
)
def faturamento_diario(
    data_inicio: datetime | None = Query(default=None),
    data_fim: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    inicio, fim = _periodo_padrao(data_inicio, data_fim)
    dados = crud.faturamento_diario(db, inicio, fim)
    return [
        schemas.FaturamentoDiarioItem(data=dia.isoformat(), total=total)
        for dia, total in dados
    ]


@router.get(
    "/produtos-mais-vendidos", response_model=list[schemas.ProdutoMaisVendidoItem]
)
def produtos_mais_vendidos(
    data_inicio: datetime | None = Query(default=None),
    data_fim: datetime | None = Query(default=None),
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    inicio, fim = _periodo_padrao(data_inicio, data_fim)
    dados = crud.produtos_mais_vendidos(db, inicio, fim, limite)
    return [
        schemas.ProdutoMaisVendidoItem(produto_nome=nome, quantidade_total=total)
        for nome, total in dados
    ]
