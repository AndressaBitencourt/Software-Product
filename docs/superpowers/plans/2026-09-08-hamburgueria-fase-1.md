# Fase 1 — Sistema de Pedidos da Hamburgueria — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um app web funcional (front + back + banco) com CRUD completo de pedidos de uma hamburgueria, rodável em macOS e Windows.

**Architecture:** Back-end FastAPI expõe uma API REST sob `/api`; SQLAlchemy 2.x mapeia três tabelas (`produto`, `pedido`, `item_pedido`) num arquivo SQLite. O mesmo processo FastAPI serve o front-end estático (HTML/CSS/JS puro) na raiz `/`. O front consome a API via `fetch` e re-renderiza a tela sem recarregar. Camadas isoladas: `models` (banco) → `schemas` (contrato HTTP) → `crud` (regras + acesso a dados) → `serializers` (monta as respostas com campos calculados) → `routers` (traduz HTTP).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, SQLite, Pydantic v2, pytest + httpx (TestClient), Docker + docker-compose.

## Global Constraints

- Python **3.12**; todo o back-end em `backend/`, front em `frontend/`.
- Banco: **SQLite** via SQLAlchemy ORM. Nada de SQL cru fora do ORM. Sem serviço externo.
- Dinheiro: coluna `Numeric(10, 2)`; `Decimal` no Python; **string com 2 casas** no JSON (`"18.00"`).
- API sob o prefixo `/api`. Erros no formato padrão do FastAPI: `{"detail": "<mensagem em português>"}`.
- `preco_unitario` e `total` são **sempre** calculados no servidor; valor de preço vindo do cliente é ignorado.
- Datas em UTC, formato ISO-8601.
- Front-end sem build, sem Node, sem framework, sem CDN — só arquivos estáticos servidos pelo FastAPI.
- Todo o trabalho da Fase 1 vai na branch `fase-1` (criada no Task 1), com um commit por passo de "Commit".
- Cada teste roda com: `cd backend && pytest`.
- Escopo travado: **só o que está neste plano**. Sem CRUD de produtos, sem mudança de status, sem login, sem relatórios (fases 2–5).

---

## Estrutura de arquivos

```
backend/
  pytest.ini                  # pythonpath=. , testpaths=tests
  requirements.txt
  app/
    __init__.py
    database.py               # engine, SessionLocal, Base, get_db, PRAGMA FK
    models.py                 # Produto, Pedido, ItemPedido, utcnow()
    schemas.py                # Money, ProdutoOut, ItemPedidoIn, PedidoIn, ItemPedidoOut, PedidoOut, PedidoResumo
    seed.py                   # CARDAPIO_INICIAL, seed_cardapio(db) -> int
    crud.py                   # RegraNegocioError + funções de acesso a dados
    serializers.py            # pedido_para_out, pedido_para_resumo
    routers/
      __init__.py
      produtos.py             # GET /api/produtos, GET /api/produtos/{id}
      pedidos.py              # POST/GET/GET{id}/PUT/DELETE /api/pedidos
    main.py                   # create_app(inicializar) + lifespan + app + /api/health + mount estático
  tests/
    conftest.py               # fixtures db_session e client
    test_health.py
    test_produtos.py
    test_pedidos.py
frontend/
  index.html
  styles.css
  app.js
Dockerfile
docker-compose.yml
.dockerignore
README.md
```

---

## Task 1: Scaffold + banco + modelos + health

**Files:**
- Create: `backend/pytest.ini`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py` (vazio)
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `app.database.Base` — declarative base.
  - `app.database.engine` — Engine SQLite do processo real.
  - `app.database.SessionLocal` — factory de `Session`.
  - `app.database.get_db() -> Iterator[Session]` — dependência FastAPI.
  - `app.models.utcnow() -> datetime` (aware, UTC).
  - `app.models.Produto(id, nome, descricao, preco, categoria, disponivel)`.
  - `app.models.Pedido(id, cliente_nome, observacao, status, criado_em, atualizado_em, itens: list[ItemPedido])`.
  - `app.models.ItemPedido(id, pedido_id, produto_id, quantidade, preco_unitario, pedido, produto)`.
  - `app.main.inicializar_banco() -> None` — cria as tabelas (`Base.metadata.create_all`) e roda o seed; chamado só no startup do servidor real.
  - `app.main.create_app(inicializar: bool = True) -> FastAPI` — com `inicializar=True` registra um `lifespan` que chama `inicializar_banco()` quando o servidor sobe (nunca no import). Testes usam `inicializar=False`.
  - `app.main.app` — instância default (`create_app()`), usada por `uvicorn app.main:app`.
  - Fixtures pytest: `db_session` (Session em SQLite `:memory:` com todas as tabelas criadas e `PRAGMA foreign_keys=ON`) e `client` (`TestClient` cujo `get_db` devolve `db_session`).

- [ ] **Step 1: Criar a branch de trabalho**

```bash
git checkout -b fase-1
```

- [ ] **Step 2: `backend/requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.4
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 3: `backend/pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 4: `backend/app/__init__.py`**

Arquivo vazio (marca `app` como pacote).

- [ ] **Step 5: `backend/app/database.py`**

```python
import os
from pathlib import Path
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent  # backend/
DB_DIR = Path(os.environ.get("DB_DIR", str(DEFAULT_DB_DIR)))
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: `backend/app/models.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    descricao: Mapped[str | None] = mapped_column(String(255), default=None)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    categoria: Mapped[str] = mapped_column(String(40))
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)


class Pedido(Base):
    __tablename__ = "pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_nome: Mapped[str] = mapped_column(String(80))
    observacao: Mapped[str | None] = mapped_column(String(255), default=None)
    status: Mapped[str] = mapped_column(String(20), default="recebido")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ItemPedido(Base):
    __tablename__ = "item_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedido.id", ondelete="CASCADE")
    )
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    quantidade: Mapped[int] = mapped_column()
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship(lazy="joined")
```

- [ ] **Step 7: `backend/app/main.py`**

```python
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

    # os routers de produtos e pedidos são incluídos aqui nos tasks seguintes.

    if FRONTEND_DIR.is_dir():
        app.mount(
            "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
        )

    return app


app = create_app()
```

Notas:
- `from app import models` no topo garante que `Base.metadata` conhece as três tabelas antes de qualquer `create_all` — sem isso, `uvicorn app.main:app` subiria com um banco sem tabelas.
- Criação de tabelas + seed acontecem **só no `lifespan`** (startup do servidor). Importar `app.main` (o que os testes fazem) não toca em disco nem em banco.
- `from app.seed import ...` fica dentro de `inicializar_banco` de propósito: `seed.py` só existe a partir do Task 2, e nada chama `inicializar_banco` antes disso (a fixture `client` usa `inicializar=False`). **Não criar stub de `seed.py` no Task 1.**

- [ ] **Step 8: `backend/tests/conftest.py`**

```python
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app


@pytest.fixture
def db_session() -> Iterator[Session]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _fk_on(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(test_engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app(inicializar=False)

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

- [ ] **Step 9: `backend/tests/test_health.py` (teste que falha)**

```python
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_modelos_criam_e_consultam(db_session: Session) -> None:
    produto = models.Produto(
        nome="X-Teste", descricao="teste", preco=10, categoria="Teste"
    )
    db_session.add(produto)
    db_session.commit()

    achado = db_session.query(models.Produto).filter_by(nome="X-Teste").one()
    assert achado.id is not None
    assert achado.disponivel is True
```

- [ ] **Step 10: Rodar e ver falhar**

Run: `cd backend && pip install -r requirements.txt && pytest -v`
Expected: coleta falha ou os testes falham (`ModuleNotFoundError` / arquivos ausentes) até todos os arquivos acima existirem. Depois de criados, deve **passar**.

- [ ] **Step 11: Rodar e ver passar**

Run: `cd backend && pytest -v`
Expected: `test_health_ok` e `test_modelos_criam_e_consultam` PASS.

- [ ] **Step 12: Commit**

```bash
git add backend/
git commit -m "feat: scaffold do backend, modelos ORM e endpoint /api/health"
```

---

## Task 2: Seed do cardápio

**Files:**
- Create: `backend/app/seed.py`
- Create: `backend/tests/test_produtos.py` (só a parte de seed neste task)
- Modify: `backend/tests/conftest.py` (adicionar seed à fixture `client`)

**Interfaces:**
- Consumes: `app.models.Produto`, fixture `db_session`, fixture `client`.
- Produces:
  - `app.seed.CARDAPIO_INICIAL: list[dict]` — 8 itens (`nome`, `descricao`, `preco: Decimal`, `categoria`).
  - `app.seed.seed_cardapio(db: Session) -> int` — insere os 8 itens **se a tabela estiver vazia**; devolve quantos inseriu (0 se já havia).
  - A fixture `client` passa a ter o cardápio de 8 itens carregado (ids 1..8 na ordem de `CARDAPIO_INICIAL`).

- [ ] **Step 1: `backend/tests/test_produtos.py` (teste que falha)**

```python
from sqlalchemy.orm import Session

from app import models
from app.seed import CARDAPIO_INICIAL, seed_cardapio


def test_seed_popula_oito_itens(db_session: Session) -> None:
    inseridos = seed_cardapio(db_session)
    assert inseridos == 8
    assert db_session.query(models.Produto).count() == 8


def test_seed_e_idempotente(db_session: Session) -> None:
    assert seed_cardapio(db_session) == 8
    assert seed_cardapio(db_session) == 0
    assert db_session.query(models.Produto).count() == 8


def test_cardapio_inicial_tem_quatro_categorias(db_session: Session) -> None:
    categorias = {item["categoria"] for item in CARDAPIO_INICIAL}
    assert categorias == {
        "Clássicos",
        "Especiais",
        "Acompanhamentos",
        "Bebidas",
    }
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_produtos.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.seed'`.

- [ ] **Step 3: `backend/app/seed.py`**

```python
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models

CARDAPIO_INICIAL: list[dict] = [
    {"nome": "X-Salada", "descricao": "Hambúrguer, queijo, alface, tomate e maionese",
     "preco": Decimal("18.00"), "categoria": "Clássicos"},
    {"nome": "X-Bacon", "descricao": "Hambúrguer, queijo, bacon crocante e maionese",
     "preco": Decimal("22.00"), "categoria": "Clássicos"},
    {"nome": "X-Tudo", "descricao": "Dois hambúrgueres, queijo, bacon, ovo, salada e batata palha",
     "preco": Decimal("28.00"), "categoria": "Especiais"},
    {"nome": "X-Vegetariano", "descricao": "Hambúrguer de grão-de-bico, queijo, rúcula e tomate seco",
     "preco": Decimal("24.00"), "categoria": "Especiais"},
    {"nome": "Batata Frita", "descricao": "Porção individual de batata frita",
     "preco": Decimal("12.00"), "categoria": "Acompanhamentos"},
    {"nome": "Onion Rings", "descricao": "Anéis de cebola empanados",
     "preco": Decimal("14.00"), "categoria": "Acompanhamentos"},
    {"nome": "Refrigerante Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas"},
    {"nome": "Suco Natural", "descricao": "Copo 300 ml, sabores do dia",
     "preco": Decimal("9.00"), "categoria": "Bebidas"},
]


def seed_cardapio(db: Session) -> int:
    ja_existem = db.scalar(select(func.count()).select_from(models.Produto))
    if ja_existem:
        return 0
    db.add_all(models.Produto(**item) for item in CARDAPIO_INICIAL)
    db.commit()
    return len(CARDAPIO_INICIAL)
```

- [ ] **Step 4: Ligar o seed na fixture `client`**

Em `backend/tests/conftest.py`, dentro da fixture `client`, logo após `app = create_app(...)` e antes do `TestClient`, adicionar:

```python
    from app.seed import seed_cardapio

    seed_cardapio(db_session)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `cd backend && pytest -v`
Expected: todos os testes de `test_health.py` e `test_produtos.py` PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: seed idempotente do cardapio com 8 itens"
```

---

## Task 3: Schemas + endpoints de leitura do cardápio

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/crud.py`
- Create: `backend/app/routers/__init__.py` (vazio)
- Create: `backend/app/routers/produtos.py`
- Modify: `backend/app/main.py` (incluir o router de produtos)
- Modify: `backend/tests/test_produtos.py` (adicionar testes de API)

**Interfaces:**
- Consumes: `app.models`, `app.database.get_db`, fixture `client`.
- Produces:
  - `app.schemas.Money` — `Annotated[Decimal, PlainSerializer(-> "0.00")]`.
  - `app.schemas.ProdutoOut(id, nome, descricao, preco, categoria, disponivel)` (`from_attributes=True`).
  - `app.crud.RegraNegocioError(Exception)` com atributo `.mensagem: str`.
  - `app.crud.listar_produtos(db, incluir_indisponiveis: bool = False) -> list[models.Produto]` (ordenado por categoria, nome).
  - `app.crud.obter_produto(db, produto_id: int) -> models.Produto | None`.
  - `app.routers.produtos.router` — `APIRouter(prefix="/api/produtos")`.
  - Rotas: `GET /api/produtos?incluir_indisponiveis=<bool>` e `GET /api/produtos/{produto_id}`.

- [ ] **Step 1: Testes de API (que falham)**

Adicionar ao fim de `backend/tests/test_produtos.py`:

```python
from fastapi.testclient import TestClient


def test_get_produtos_retorna_seed(client: TestClient) -> None:
    resp = client.get("/api/produtos")
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 8
    primeiro = corpo[0]
    assert set(primeiro) == {
        "id", "nome", "descricao", "preco", "categoria", "disponivel"
    }
    assert isinstance(primeiro["preco"], str)
    assert primeiro["preco"].count(".") == 1


def test_get_produtos_esconde_indisponivel_por_padrao(client: TestClient) -> None:
    from app import models

    resp_antes = client.get("/api/produtos")
    assert len(resp_antes.json()) == 8

    # marca o produto 1 como indisponível direto no banco de teste
    db = client.app.dependency_overrides  # sanity: override existe
    assert db

    from tests.conftest import db_session  # type: ignore  # noqa

    # feito via a própria fixture no teste abaixo


def test_get_produtos_incluir_indisponiveis(client: TestClient, db_session) -> None:
    from app import models

    produto = db_session.get(models.Produto, 1)
    produto.disponivel = False
    db_session.commit()

    padrao = client.get("/api/produtos")
    assert len(padrao.json()) == 7

    completo = client.get("/api/produtos", params={"incluir_indisponiveis": "true"})
    assert len(completo.json()) == 8


def test_get_produto_por_id(client: TestClient) -> None:
    resp = client.get("/api/produtos/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_get_produto_inexistente_404(client: TestClient) -> None:
    resp = client.get("/api/produtos/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Produto não encontrado."
```

Remover a função-rascunho `test_get_produtos_esconde_indisponivel_por_padrao` — foi substituída por `test_get_produtos_incluir_indisponiveis`. (Não deixar rascunho no arquivo.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_produtos.py -v`
Expected: FAIL — `No module named 'app.schemas'` / 404 nas rotas novas.

- [ ] **Step 3: `backend/app/schemas.py`**

```python
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
```

- [ ] **Step 4: `backend/app/crud.py`**

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
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


def _montar_itens(
    db: Session, itens_in: list[schemas.ItemPedidoIn]
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
        if not produto.disponivel:
            raise RegraNegocioError(
                f"Produto '{produto.nome}' está indisponível."
            )
        itens.append(
            models.ItemPedido(
                produto_id=produto.id,
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


def listar_pedidos(db: Session) -> list[models.Pedido]:
    stmt = select(models.Pedido).order_by(models.Pedido.criado_em.desc())
    return list(db.scalars(stmt))


def obter_pedido(db: Session, pedido_id: int) -> models.Pedido | None:
    return db.get(models.Pedido, pedido_id)


def atualizar_pedido(
    db: Session, pedido_id: int, dados: schemas.PedidoIn
) -> models.Pedido | None:
    pedido = db.get(models.Pedido, pedido_id)
    if pedido is None:
        return None
    novos_itens = _montar_itens(db, dados.itens)
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
```

Nota: `crud.py` já traz todas as funções de pedido — os Tasks 4–7 só ligam os endpoints. Isso evita reescrever o arquivo a cada task.

- [ ] **Step 5: `backend/app/routers/__init__.py`**

Arquivo vazio.

- [ ] **Step 6: `backend/app/routers/produtos.py`**

```python
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
```

- [ ] **Step 7: Registrar o router em `backend/app/main.py`**

Depois da definição de `health`, antes do bloco `if FRONTEND_DIR.is_dir()`:

```python
    from app.routers import produtos

    app.include_router(produtos.router)
```

- [ ] **Step 8: Rodar e ver passar**

Run: `cd backend && pytest -v`
Expected: todos PASS (health + produtos).

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: schemas, camada crud e leitura do cardapio via /api/produtos"
```

---

## Task 4: Criar pedido — `POST /api/pedidos`

**Files:**
- Create: `backend/app/serializers.py`
- Create: `backend/app/routers/pedidos.py`
- Modify: `backend/app/main.py` (incluir o router de pedidos)
- Create: `backend/tests/test_pedidos.py`

**Interfaces:**
- Consumes: `app.crud` (`criar_pedido`, `RegraNegocioError`), `app.schemas`, `app.models`.
- Produces:
  - `app.serializers.pedido_para_out(pedido: models.Pedido) -> schemas.PedidoOut` — calcula `subtotal` por item e `total`.
  - `app.serializers.pedido_para_resumo(pedido: models.Pedido) -> schemas.PedidoResumo` — `quantidade_itens = soma das quantidades`, `total` calculado.
  - `app.routers.pedidos.router` — `APIRouter(prefix="/api/pedidos")`.
  - Rota `POST /api/pedidos` → 201 + `PedidoOut`; `RegraNegocioError` → 400 `{"detail": ...}`; corpo inválido → 422.

- [ ] **Step 1: `backend/app/serializers.py`**

```python
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
```

- [ ] **Step 2: `backend/tests/test_pedidos.py` (testes que falham)**

```python
from fastapi.testclient import TestClient

PEDIDO_VALIDO = {
    "cliente_nome": "Maria",
    "observacao": "sem cebola",
    "itens": [
        {"produto_id": 1, "quantidade": 2},  # X-Salada 18.00
        {"produto_id": 5, "quantidade": 1},  # Batata Frita 12.00
    ],
}


def test_criar_pedido_valido(client: TestClient) -> None:
    resp = client.post("/api/pedidos", json=PEDIDO_VALIDO)
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["cliente_nome"] == "Maria"
    assert corpo["status"] == "recebido"
    assert corpo["total"] == "48.00"
    assert len(corpo["itens"]) == 2
    item = corpo["itens"][0]
    assert item["produto_nome"] == "X-Salada"
    assert item["preco_unitario"] == "18.00"
    assert item["subtotal"] == "36.00"


def test_criar_pedido_sem_itens_400(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos", json={"cliente_nome": "Ana", "itens": []}
    )
    assert resp.status_code == 400
    assert "pelo menos um item" in resp.json()["detail"]


def test_criar_pedido_produto_inexistente_400(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 999, "quantidade": 1}]},
    )
    assert resp.status_code == 400
    assert "999" in resp.json()["detail"]


def test_criar_pedido_quantidade_zero_422(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 1, "quantidade": 0}]},
    )
    assert resp.status_code == 422


def test_criar_pedido_sem_cliente_422(client: TestClient) -> None:
    resp = client.post(
        "/api/pedidos",
        json={"itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp.status_code == 422


def test_criar_pedido_produto_indisponivel_400(client: TestClient, db_session) -> None:
    from app import models

    db_session.get(models.Produto, 1).disponivel = False
    db_session.commit()

    resp = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp.status_code == 400
    assert "indisponível" in resp.json()["detail"]
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_pedidos.py -v`
Expected: FAIL — rota `POST /api/pedidos` não existe (404) / `No module named 'app.serializers'`.

- [ ] **Step 4: `backend/app/routers/pedidos.py`**

```python
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
```

- [ ] **Step 5: Registrar o router em `backend/app/main.py`**

Junto do `include_router(produtos.router)`:

```python
    from app.routers import pedidos

    app.include_router(pedidos.router)
```

- [ ] **Step 6: Rodar e ver passar**

Run: `cd backend && pytest -v`
Expected: todos PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: criacao de pedido via POST /api/pedidos com calculo de total"
```

---

## Task 5: Listar e detalhar pedidos — `GET /api/pedidos` e `GET /api/pedidos/{id}`

**Files:**
- Modify: `backend/app/routers/pedidos.py`
- Modify: `backend/tests/test_pedidos.py`

**Interfaces:**
- Consumes: `app.crud.listar_pedidos`, `app.crud.obter_pedido`, `app.serializers`.
- Produces:
  - `GET /api/pedidos` → `list[PedidoResumo]`, ordenado do mais novo para o mais antigo.
  - `GET /api/pedidos/{pedido_id}` → `PedidoOut`; inexistente → 404 `{"detail": "Pedido não encontrado."}`.

- [ ] **Step 1: Testes que falham**

Adicionar a `backend/tests/test_pedidos.py`:

```python
def test_listar_pedidos(client: TestClient) -> None:
    client.post("/api/pedidos", json=PEDIDO_VALIDO)
    client.post(
        "/api/pedidos",
        json={"cliente_nome": "João", "itens": [{"produto_id": 2, "quantidade": 1}]},
    )

    resp = client.get("/api/pedidos")
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 2
    primeiro = corpo[0]
    assert set(primeiro) == {
        "id", "cliente_nome", "status", "quantidade_itens", "total", "criado_em"
    }
    # o mais recente (João) vem primeiro
    assert primeiro["cliente_nome"] == "João"
    assert primeiro["quantidade_itens"] == 1
    assert primeiro["total"] == "22.00"


def test_detalhar_pedido(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()

    resp = client.get(f"/api/pedidos/{criado['id']}")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["id"] == criado["id"]
    assert corpo["total"] == "48.00"
    assert len(corpo["itens"]) == 2


def test_detalhar_pedido_inexistente_404(client: TestClient) -> None:
    resp = client.get("/api/pedidos/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Pedido não encontrado."
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_pedidos.py -k "listar or detalhar" -v`
Expected: FAIL — rotas GET não existem (405/404).

- [ ] **Step 3: Implementar as rotas**

Adicionar a `backend/app/routers/pedidos.py`:

```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && pytest -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: listagem e detalhe de pedidos"
```

---

## Task 6: Editar pedido — `PUT /api/pedidos/{id}`

**Files:**
- Modify: `backend/app/routers/pedidos.py`
- Modify: `backend/tests/test_pedidos.py`

**Interfaces:**
- Consumes: `app.crud.atualizar_pedido` (já existe desde o Task 3), `app.serializers`.
- Produces:
  - `PUT /api/pedidos/{pedido_id}` com corpo `PedidoIn` → substitui `cliente_nome`, `observacao` e **a lista inteira de itens**, recalcula `total`, atualiza `atualizado_em`; devolve `PedidoOut`.
  - Pedido inexistente → 404. `RegraNegocioError` → 400. Corpo inválido → 422.

- [ ] **Step 1: Testes que falham**

Adicionar a `backend/tests/test_pedidos.py`:

```python
def test_editar_pedido_recalcula_total(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()

    novo_corpo = {
        "cliente_nome": "Maria Clara",
        "observacao": None,
        "itens": [{"produto_id": 3, "quantidade": 2}],  # X-Tudo 28.00
    }
    resp = client.put(f"/api/pedidos/{criado['id']}", json=novo_corpo)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["cliente_nome"] == "Maria Clara"
    assert len(corpo["itens"]) == 1
    assert corpo["total"] == "56.00"
    assert corpo["atualizado_em"] >= corpo["criado_em"]


def test_editar_pedido_inexistente_404(client: TestClient) -> None:
    resp = client.put(
        "/api/pedidos/999",
        json={"cliente_nome": "X", "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp.status_code == 404


def test_editar_pedido_sem_itens_400(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()
    resp = client.put(
        f"/api/pedidos/{criado['id']}",
        json={"cliente_nome": "Maria", "itens": []},
    )
    assert resp.status_code == 400
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_pedidos.py -k editar -v`
Expected: FAIL — rota PUT não existe (405).

- [ ] **Step 3: Implementar a rota**

Adicionar a `backend/app/routers/pedidos.py`:

```python
@router.put("/{pedido_id}", response_model=schemas.PedidoOut)
def atualizar(
    pedido_id: int, dados: schemas.PedidoIn, db: Session = Depends(get_db)
):
    try:
        pedido = crud.atualizar_pedido(db, pedido_id, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return serializers.pedido_para_out(pedido)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd backend && pytest -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: edicao de pedido via PUT com substituicao de itens"
```

---

## Task 7: Excluir pedido — `DELETE /api/pedidos/{id}`

**Files:**
- Modify: `backend/app/routers/pedidos.py`
- Modify: `backend/tests/test_pedidos.py`

**Interfaces:**
- Consumes: `app.crud.excluir_pedido` (já existe desde o Task 3).
- Produces:
  - `DELETE /api/pedidos/{pedido_id}` → 204 sem corpo; some da listagem; remove os `ItemPedido` associados (cascade ORM). Inexistente → 404.

- [ ] **Step 1: Testes que falham**

Adicionar a `backend/tests/test_pedidos.py`:

```python
def test_excluir_pedido(client: TestClient) -> None:
    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()

    resp = client.delete(f"/api/pedidos/{criado['id']}")
    assert resp.status_code == 204
    assert resp.content == b""

    assert client.get(f"/api/pedidos/{criado['id']}").status_code == 404
    assert client.get("/api/pedidos").json() == []


def test_excluir_pedido_remove_itens_em_cascata(
    client: TestClient, db_session
) -> None:
    from app import models

    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()
    assert db_session.query(models.ItemPedido).count() == 2

    client.delete(f"/api/pedidos/{criado['id']}")
    assert db_session.query(models.ItemPedido).count() == 0


def test_excluir_pedido_inexistente_404(client: TestClient) -> None:
    resp = client.delete("/api/pedidos/999")
    assert resp.status_code == 404
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_pedidos.py -k excluir -v`
Expected: FAIL — rota DELETE não existe (405).

- [ ] **Step 3: Implementar a rota**

Adicionar a `backend/app/routers/pedidos.py`:

```python
@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(pedido_id: int, db: Session = Depends(get_db)):
    if not crud.excluir_pedido(db, pedido_id):
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
```

- [ ] **Step 4: Rodar toda a suíte e conferir os 16+ casos**

Run: `cd backend && pytest -v`
Expected: TODOS PASS. Conferir que estão cobertos: health; seed x3; cardápio (lista, esconde indisponível, inclui indisponível, por id, 404); criar pedido (válido, sem itens, produto inexistente, quantidade 0, sem cliente, indisponível); listar; detalhar; detalhar 404; editar (recalcula, 404, sem itens); excluir (204, cascata, 404).

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: exclusao de pedido com cascade nos itens"
```

---

## Task 8: Front-end — página única de pedidos

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles.css`
- Create: `frontend/app.js`
- Create: `backend/tests/test_frontend.py`

**Interfaces:**
- Consumes: a API `/api/produtos` e `/api/pedidos` já pronta; `create_app` já monta `frontend/` em `/` quando a pasta existe.
- Produces: página em `/` que cria, lista, vê, edita e exclui pedidos via `fetch`, sem recarregar; faixa de mensagem para sucesso/erro (lê `detail`).

- [ ] **Step 1: Teste que falha (smoke do estático)**

`backend/tests/test_frontend.py`:

```python
from fastapi.testclient import TestClient


def test_raiz_serve_o_index(client: TestClient) -> None:
    # a fixture `client` já monta o front (create_app monta frontend/ se a pasta existe)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Hamburgueria" in resp.text
    assert "app.js" in resp.text
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd backend && pytest tests/test_frontend.py -v`
Expected: FAIL — `/` retorna 404 (pasta `frontend/` ainda não existe / sem `index.html`).

- [ ] **Step 3: `frontend/index.html`**

```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hamburgueria — Pedidos</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header>
    <h1>🍔 Hamburgueria — Pedidos</h1>
  </header>

  <div id="aviso" class="aviso" hidden></div>

  <main>
    <section id="secao-cardapio">
      <h2>Cardápio</h2>
      <div id="cardapio" class="cards"></div>
    </section>

    <section id="secao-form">
      <h2 id="form-titulo">Novo pedido</h2>
      <form id="form-pedido">
        <label>Cliente
          <input type="text" id="cliente_nome" maxlength="80" required />
        </label>
        <label>Observação
          <input type="text" id="observacao" maxlength="255" />
        </label>

        <h3>Itens</h3>
        <ul id="carrinho"></ul>
        <p id="carrinho-vazio">Nenhum item. Use "Adicionar" no cardápio.</p>
        <p class="total">Total: <strong id="form-total">R$ 0,00</strong></p>

        <div class="acoes">
          <button type="submit" id="btn-salvar">Fazer pedido</button>
          <button type="button" id="btn-cancelar" hidden>Cancelar edição</button>
        </div>
      </form>
    </section>

    <section id="secao-pedidos">
      <h2>Pedidos</h2>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Cliente</th><th>Itens</th><th>Total</th>
            <th>Status</th><th>Criado em</th><th></th>
          </tr>
        </thead>
        <tbody id="lista-pedidos"></tbody>
      </table>
      <p id="pedidos-vazio">Nenhum pedido ainda.</p>
    </section>
  </main>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 4: `frontend/styles.css`**

```css
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  color: #222;
  background: #faf7f2;
}
header {
  background: #b5301f;
  color: #fff;
  padding: 16px 24px;
}
header h1 { margin: 0; font-size: 1.4rem; }
main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
  display: grid;
  gap: 32px;
}
h2 { border-bottom: 2px solid #e6ddd0; padding-bottom: 4px; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.card {
  background: #fff;
  border: 1px solid #e6ddd0;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card small { color: #777; }
.card .preco { font-weight: 700; color: #b5301f; }
.card button { margin-top: auto; }
button {
  background: #b5301f;
  color: #fff;
  border: 0;
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.9rem;
}
button.secundario { background: #6c757d; }
button.perigo { background: #8a1c10; }
form label {
  display: block;
  margin-bottom: 10px;
}
form input {
  display: block;
  width: 100%;
  padding: 8px;
  margin-top: 4px;
  border: 1px solid #ccc;
  border-radius: 6px;
}
#carrinho { list-style: none; padding: 0; display: grid; gap: 6px; }
#carrinho li {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e6ddd0;
  border-radius: 6px;
  padding: 6px 10px;
}
#carrinho li span { flex: 1; }
#carrinho li input { width: 64px; }
table { width: 100%; border-collapse: collapse; background: #fff; }
th, td { border: 1px solid #e6ddd0; padding: 8px; text-align: left; font-size: 0.9rem; }
.acoes { display: flex; gap: 8px; }
.aviso {
  max-width: 960px;
  margin: 12px auto 0;
  padding: 10px 16px;
  border-radius: 6px;
}
.aviso.erro { background: #f8d7da; color: #842029; }
.aviso.ok { background: #d1e7dd; color: #0f5132; }
.detalhe-itens { background: #fbf6ee; }
@media (max-width: 600px) {
  table, thead, tbody, th, td, tr { display: block; }
  thead { display: none; }
  td { border: 0; border-bottom: 1px solid #eee; }
}
```

- [ ] **Step 5: `frontend/app.js`**

```javascript
"use strict";

const API = "/api";
let cardapio = [];
let carrinho = []; // [{ produto_id, nome, preco, quantidade }]
let editandoId = null;

const $ = (sel) => document.querySelector(sel);

function aviso(msg, tipo) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso " + tipo;
  el.hidden = false;
  if (tipo === "ok") setTimeout(() => (el.hidden = true), 3000);
}

function brl(valorStr) {
  const n = Number(valorStr || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function api(caminho, opcoes) {
  const resp = await fetch(API + caminho, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (resp.status === 204) return null;
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detalhe = corpo.detail;
    const msg = Array.isArray(detalhe)
      ? detalhe.map((d) => d.msg).join("; ")
      : detalhe || "Erro inesperado.";
    throw new Error(msg);
  }
  return corpo;
}

async function carregarCardapio() {
  cardapio = await api("/produtos");
  const box = $("#cardapio");
  box.innerHTML = "";
  for (const p of cardapio) {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <strong>${p.nome}</strong>
      <small>${p.categoria}</small>
      <span>${p.descricao ?? ""}</span>
      <span class="preco">${brl(p.preco)}</span>
      <button type="button" data-id="${p.id}">Adicionar</button>`;
    div.querySelector("button").addEventListener("click", () => adicionar(p.id));
    box.appendChild(div);
  }
}

function adicionar(produtoId) {
  const prod = cardapio.find((p) => p.id === produtoId);
  const existente = carrinho.find((i) => i.produto_id === produtoId);
  if (existente) existente.quantidade += 1;
  else
    carrinho.push({
      produto_id: prod.id,
      nome: prod.nome,
      preco: prod.preco,
      quantidade: 1,
    });
  renderCarrinho();
}

function renderCarrinho() {
  const ul = $("#carrinho");
  ul.innerHTML = "";
  let total = 0;
  carrinho.forEach((item, idx) => {
    total += Number(item.preco) * item.quantidade;
    const li = document.createElement("li");
    li.innerHTML = `
      <span>${item.nome}</span>
      <input type="number" min="1" value="${item.quantidade}" />
      <button type="button" class="perigo">x</button>`;
    li.querySelector("input").addEventListener("change", (e) => {
      const q = parseInt(e.target.value, 10);
      item.quantidade = Number.isNaN(q) || q < 1 ? 1 : q;
      renderCarrinho();
    });
    li.querySelector("button").addEventListener("click", () => {
      carrinho.splice(idx, 1);
      renderCarrinho();
    });
    ul.appendChild(li);
  });
  $("#carrinho-vazio").hidden = carrinho.length > 0;
  $("#form-total").textContent = brl(total.toFixed(2));
}

function entrarModoEdicao(pedido) {
  editandoId = pedido.id;
  $("#form-titulo").textContent = `Editar pedido #${pedido.id}`;
  $("#btn-salvar").textContent = "Salvar alterações";
  $("#btn-cancelar").hidden = false;
  $("#cliente_nome").value = pedido.cliente_nome;
  $("#observacao").value = pedido.observacao ?? "";
  carrinho = pedido.itens.map((i) => ({
    produto_id: i.produto_id,
    nome: i.produto_nome,
    preco: i.preco_unitario,
    quantidade: i.quantidade,
  }));
  renderCarrinho();
  $("#secao-form").scrollIntoView({ behavior: "smooth" });
}

function sairModoEdicao() {
  editandoId = null;
  $("#form-titulo").textContent = "Novo pedido";
  $("#btn-salvar").textContent = "Fazer pedido";
  $("#btn-cancelar").hidden = true;
  $("#form-pedido").reset();
  carrinho = [];
  renderCarrinho();
}

async function submeter(evento) {
  evento.preventDefault();
  const payload = {
    cliente_nome: $("#cliente_nome").value.trim(),
    observacao: $("#observacao").value.trim() || null,
    itens: carrinho.map((i) => ({
      produto_id: i.produto_id,
      quantidade: i.quantidade,
    })),
  };
  try {
    if (editandoId) {
      await api(`/pedidos/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      aviso("Pedido atualizado.", "ok");
    } else {
      await api("/pedidos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      aviso("Pedido criado.", "ok");
    }
    sairModoEdicao();
    await carregarPedidos();
  } catch (e) {
    aviso(e.message, "erro");
  }
}

async function carregarPedidos() {
  const pedidos = await api("/pedidos");
  const tbody = $("#lista-pedidos");
  tbody.innerHTML = "";
  $("#pedidos-vazio").hidden = pedidos.length > 0;
  for (const p of pedidos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.cliente_nome}</td>
      <td>${p.quantidade_itens}</td>
      <td>${brl(p.total)}</td>
      <td>${p.status}</td>
      <td>${new Date(p.criado_em).toLocaleString("pt-BR")}</td>
      <td></td>`;
    const acoes = tr.lastElementChild;

    const bVer = document.createElement("button");
    bVer.textContent = "Ver";
    bVer.className = "secundario";
    bVer.addEventListener("click", () => verDetalhe(p.id, tr));

    const bEditar = document.createElement("button");
    bEditar.textContent = "Editar";
    bEditar.addEventListener("click", async () => {
      try {
        entrarModoEdicao(await api(`/pedidos/${p.id}`));
      } catch (e) {
        aviso(e.message, "erro");
      }
    });

    const bExcluir = document.createElement("button");
    bExcluir.textContent = "Excluir";
    bExcluir.className = "perigo";
    bExcluir.addEventListener("click", async () => {
      if (!confirm(`Excluir o pedido #${p.id}?`)) return;
      try {
        await api(`/pedidos/${p.id}`, { method: "DELETE" });
        aviso("Pedido excluído.", "ok");
        await carregarPedidos();
      } catch (e) {
        aviso(e.message, "erro");
      }
    });

    acoes.append(bVer, bEditar, bExcluir);
    tbody.appendChild(tr);
  }
}

async function verDetalhe(pedidoId, linha) {
  const proxima = linha.nextElementSibling;
  if (proxima && proxima.classList.contains("detalhe-itens")) {
    proxima.remove();
    return;
  }
  try {
    const p = await api(`/pedidos/${pedidoId}`);
    const tr = document.createElement("tr");
    tr.className = "detalhe-itens";
    const linhas = p.itens
      .map(
        (i) =>
          `${i.quantidade}x ${i.produto_nome} — ${brl(i.preco_unitario)} (subtotal ${brl(i.subtotal)})`
      )
      .join("<br />");
    tr.innerHTML = `<td colspan="7">${linhas}<br /><strong>Total: ${brl(p.total)}</strong>${
      p.observacao ? "<br />Obs.: " + p.observacao : ""
    }</td>`;
    linha.after(tr);
  } catch (e) {
    aviso(e.message, "erro");
  }
}

$("#form-pedido").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);

(async function iniciar() {
  try {
    await carregarCardapio();
    await carregarPedidos();
    renderCarrinho();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
```

- [ ] **Step 6: Rodar o smoke test e ver passar**

Run: `cd backend && pytest -v`
Expected: todos PASS, incluindo `test_raiz_serve_o_index`.

- [ ] **Step 7: Teste manual no navegador**

```bash
cd backend && uvicorn app.main:app --reload
```

Abrir `http://localhost:8000` e conferir:
- cardápio aparece com 8 itens;
- adicionar 2 itens, alterar quantidade, criar pedido → aparece na tabela com total certo;
- "Ver" expande os itens; clicar de novo recolhe;
- "Editar" carrega o pedido no formulário; salvar altera o total na tabela;
- "Excluir" pede confirmação e remove a linha;
- enviar sem cliente ou sem itens → faixa vermelha com a mensagem da API;
- `http://localhost:8000/docs` abre o Swagger.

Parar o servidor (`Ctrl+C`). Apagar o `backend/app.db` gerado (`git status` deve ficar limpo — ele está no `.gitignore`).

- [ ] **Step 8: Commit**

```bash
git add frontend/ backend/tests/test_frontend.py
git commit -m "feat: pagina unica de pedidos (cardapio, carrinho, CRUD via fetch)"
```

---

## Task 9: Docker, execução multiplataforma e README

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `README.md`

**Interfaces:**
- Consumes: `backend/` e `frontend/` prontos; `app.database` lê `DB_DIR` do ambiente; `app.main` lê `FRONTEND_DIR` do ambiente.
- Produces: `docker compose up --build` sobe o app em `http://localhost:8000` em macOS e Windows, com o banco persistido num volume.

- [ ] **Step 1: `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY frontend ./frontend

RUN mkdir -p /app/data
ENV DB_DIR=/app/data
ENV FRONTEND_DIR=/app/frontend
ENV PYTHONPATH=/app/backend

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: `docker-compose.yml`**

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_DIR=/app/data
    volumes:
      - db-data:/app/data

volumes:
  db-data:
```

- [ ] **Step 3: `.dockerignore`**

```
**/__pycache__
**/*.pyc
.venv
venv
*.db
.git
.gitignore
.pytest_cache
docs
```

- [ ] **Step 4: `README.md`**

```markdown
# Software-Product — Sistema de Pedidos da Hamburgueria

Trabalho de faculdade entregue em 5 fases. **Fase 1:** CRUD completo de pedidos
com front-end, back-end e banco de dados.

## Tecnologias

- Back-end: Python 3.12 + FastAPI
- Banco: SQLite (arquivo `app.db`) via SQLAlchemy
- Front-end: HTML + CSS + JavaScript puro (sem build)
- Testes: pytest
- Empacotamento: Docker + docker-compose

## Como rodar

### Opção A — Docker (recomendada, igual em macOS e Windows)

Pré-requisito: Docker Desktop instalado e aberto.

```
docker compose up --build
```

Acesse:
- App: http://localhost:8000
- API (Swagger): http://localhost:8000/docs

Os pedidos ficam salvos no volume `db-data` mesmo parando o container.
Para zerar os dados: `docker compose down -v`.

### Opção B — Sem Docker

Pré-requisito: Python 3.12+.

macOS / Linux:

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows (PowerShell):

```
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse http://localhost:8000. O arquivo `backend/app.db` é criado sozinho na
primeira execução e populado com o cardápio inicial.

## Rodar os testes

```
cd backend
pip install -r requirements.txt
pytest -v
```

## Estrutura

- `backend/app/` — API FastAPI (models, schemas, crud, serializers, routers)
- `backend/tests/` — testes automatizados
- `frontend/` — página única servida pelo próprio back-end
- `docs/superpowers/` — spec e plano de implementação

## Roadmap

| Fase | Funcionalidade |
|---|---|
| 1 | CRUD de pedidos (esta entrega) |
| 2 | Gestão de cardápio (CRUD de produtos) |
| 3 | Fluxo de status do pedido + conta detalhada |
| 4 | Login e perfis (cliente / atendente) |
| 5 | Relatórios e dashboard |
```

- [ ] **Step 5: Validar o build Docker**

Run:
```bash
docker compose up --build -d
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/ | grep -o "Hamburgueria — Pedidos"
curl -s http://localhost:8000/api/produtos | head -c 120
docker compose down
```
Expected: `{"status":"ok"}`; a string do título; um JSON com produtos.

- [ ] **Step 6: Rodar a suíte de novo (nada quebrou)**

Run: `cd backend && pytest -v`
Expected: todos PASS.

- [ ] **Step 7: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore README.md
git commit -m "chore: empacotamento Docker, README e execucao multiplataforma"
```

---

## Task 10: Fechamento da Fase 1

**Files:** nenhum novo — verificação e integração.

- [ ] **Step 1: Verificação final**

Run: `cd backend && pytest -v`
Expected: 100% PASS.

Conferир manualmente uma última vez pelo navegador (criar / ver / editar / excluir) usando `docker compose up` **ou** `uvicorn`.

- [ ] **Step 2: Push da branch**

```bash
git push -u origin fase-1
```

- [ ] **Step 3: Abrir o Pull Request**

```bash
gh pr create --base main --head fase-1 \
  --title "Fase 1 — CRUD de pedidos da hamburgueria" \
  --body "$(cat <<'EOF'
## Fase 1 — CRUD completo de pedidos

Entrega da primeira das cinco fases.

### O que tem
- API FastAPI sob `/api`: cardápio (leitura) e pedidos (POST, GET lista, GET detalhe, PUT, DELETE)
- Banco SQLite via SQLAlchemy (`produto`, `pedido`, `item_pedido`), seed de 8 itens
- Página única (HTML/CSS/JS puro) servida pelo back-end: cardápio, carrinho, lista de pedidos com ver/editar/excluir
- Total e preço unitário calculados no servidor
- Suíte de testes com pytest cobrindo os casos de sucesso e de erro
- `docker compose up` roda igual em macOS e Windows

### Como testar
`cd backend && pip install -r requirements.txt && pytest -v`
ou `docker compose up --build` e abrir http://localhost:8000

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Avisar que a Fase 1 está pronta para revisão/merge**

O merge para `main` fica a critério de vocês (a próxima fase parte de `main` já com a Fase 1 mergeada).

---

## Self-Review (feito pelo autor do plano)

**1. Cobertura do spec:**
- §2 stack → Tasks 1, 8, 9. ✔
- §3 estrutura de pastas → seção "Estrutura de arquivos" + Tasks. ✔
- §4 modelo de dados (Produto/Pedido/ItemPedido, seed 8 itens) → Tasks 1 e 2. ✔
- §5 endpoints (health, produtos x2, pedidos x5) → Tasks 1, 3, 4, 5, 6, 7. ✔
- §5 regras de negócio (≥1 item, quantidade ≥1, produto existe, indisponível, preço server-side, PUT substitui itens) → Task 4 (crud `_montar_itens`) e Task 6. ✔
- §6 front-end (3 seções, sem reload, faixa de erro lendo `detail`) → Task 8. ✔
- §7 tratamento de erros (422 Pydantic, 400/404 negócio, sessão por request) → `get_db` (Task 1), `RegraNegocioError` (Task 3), routers (Tasks 4–7). ✔
- §8 testes (16 casos) → distribuídos nos Tasks 1–8; conferência explícita no Task 7 Step 4. ✔
- §9 execução Docker + venv + `.gitignore` → Task 9 (o `.gitignore` já foi commitado no repo antes do plano). ✔
- §10 fora de escopo → "Global Constraints" trava o escopo. ✔
- §11 riscos (Money como string, volume do db) → `Money` no schema (Task 3), volume no compose (Task 9). ✔

**2. Placeholders:** nenhum "TBD"/"TODO"; todo passo de código traz o código real. ✔

**3. Consistência de tipos:** `RegraNegocioError.mensagem`, `seed_cardapio(db) -> int`, `create_app(inicializar)` + `inicializar_banco()`, `pedido_para_out` / `pedido_para_resumo`, `Money` — nomes idênticos entre a definição (Tasks 1–4) e o uso (Tasks 4–8). `crud.py` é escrito inteiro no Task 3, então `atualizar_pedido`/`excluir_pedido` já existem quando os Tasks 6 e 7 ligam as rotas. ✔
