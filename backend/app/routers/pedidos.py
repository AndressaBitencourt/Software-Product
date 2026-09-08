from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas, serializers
from app.database import get_db

router = APIRouter(prefix="/api/pedidos", tags=["pedidos"])


@router.post(
    "", response_model=schemas.PedidoOut, status_code=status.HTTP_201_CREATED
)
def criar(dados: schemas.PedidoIn, db: Session = Depends(get_db)):
    try:
        pedido = crud.criar_pedido(db, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    return serializers.pedido_para_out(pedido)


@router.get("", response_model=list[schemas.PedidoResumo])
def listar(db: Session = Depends(get_db)):
    return [
        serializers.pedido_para_resumo(p) for p in crud.listar_pedidos(db)
    ]


@router.get("/{pedido_id}", response_model=schemas.PedidoOut)
def detalhar(pedido_id: int, db: Session = Depends(get_db)):
    pedido = crud.obter_pedido(db, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return serializers.pedido_para_out(pedido)
