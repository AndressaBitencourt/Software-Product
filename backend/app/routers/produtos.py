from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


@router.get("", response_model=list[schemas.ProdutoOut])
def listar(
    incluir_indisponiveis: bool = False, db: Session = Depends(get_db)
) -> list:
    return crud.listar_produtos(db, incluir_indisponiveis)


@router.get("/{produto_id}", response_model=schemas.ProdutoOut)
def detalhar(produto_id: int, db: Session = Depends(get_db)):
    produto = crud.obter_produto(db, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto
