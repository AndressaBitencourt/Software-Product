import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine

_DEFAULT_FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", str(_DEFAULT_FRONTEND)))


def create_app(create_tables: bool = True, run_seed: bool = True) -> FastAPI:
    app = FastAPI(title="Hamburgueria — Pedidos", version="1.0.0")

    if create_tables:
        Base.metadata.create_all(engine)

    if run_seed:
        from app.seed import seed_cardapio

        db = SessionLocal()
        try:
            seed_cardapio(db)
        finally:
            db.close()

    @app.get("/api/health", tags=["infra"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    if FRONTEND_DIR.is_dir():
        app.mount(
            "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
        )

    return app


app = create_app()
