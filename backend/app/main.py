import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  -- registra as tabelas em Base.metadata
from app.database import Base, SessionLocal, engine

_DEFAULT_FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", str(_DEFAULT_FRONTEND)))


def inicializar_banco() -> None:
    """Cria as tabelas e popula o cardápio. Só roda no startup do servidor real."""
    Base.metadata.create_all(engine)
    from app.seed import seed_cardapio

    db = SessionLocal()
    try:
        seed_cardapio(db)
    finally:
        db.close()


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    inicializar_banco()
    yield


def create_app(inicializar: bool = True) -> FastAPI:
    app = FastAPI(
        title="Hamburgueria — Pedidos",
        version="1.0.0",
        lifespan=_lifespan if inicializar else None,
    )

    @app.get("/api/health", tags=["infra"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    from app.routers import produtos

    app.include_router(produtos.router)

    from app.routers import pedidos

    app.include_router(pedidos.router)

    if FRONTEND_DIR.is_dir():
        app.mount(
            "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
        )

    return app


app = create_app()
