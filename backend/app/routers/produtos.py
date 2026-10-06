from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


@router.get("", response_model=list[schemas.ProdutoOut])
def listar(
    incluir_indisponiveis: bool = False, db: Session = Depends(get_db)
) -> list[models.Produto]:
    return crud.listar_produtos(db, incluir_indisponiveis)


@router.get("/{produto_id}", response_model=schemas.ProdutoOut)
def detalhar(produto_id: int, db: Session = Depends(get_db)):
    produto = crud.obter_produto(db, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@router.post(
    "", response_model=schemas.ProdutoOut, status_code=status.HTTP_201_CREATED
)
def criar(dados: schemas.ProdutoIn, db: Session = Depends(get_db)):
    try:
        produto = crud.criar_produto(db, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    return produto


@router.put("/{produto_id}", response_model=schemas.ProdutoOut)
def atualizar(
    produto_id: int, dados: schemas.ProdutoIn, db: Session = Depends(get_db)
):
    try:
        produto = crud.atualizar_produto(db, produto_id, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(produto_id: int, db: Session = Depends(get_db)):
    try:
        encontrou = crud.excluir_produto(db, produto_id)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    if not encontrou:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
