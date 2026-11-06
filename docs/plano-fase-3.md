# Fase 3 — Login e Perfis + Relatórios — Plano de implementação

> Uso o skill `subagent-driven-development` (recomendado) ou `executing-plans`
> pra seguir esse plano tarefa por tarefa. Os passos usam `- [ ]` pra eu
> marcar conforme termino.

**Objetivo:** autenticação com papéis (atendente / admin) e rotas
protegidas, mais uma tela de relatórios (faturamento, produtos mais
vendidos, busca e filtros) com gráficos simples.

**Arquitetura:** mesmas camadas das fases anteriores (`models` → `schemas` →
`crud` → `routers`). Autenticação por sessão em tabela (não JWT) com cookie
`HttpOnly` + `SameSite=Lax`. A proteção de verdade é sempre na API — as
páginas HTML continuam estáticas, e cada uma confere a sessão via
`GET /api/me` assim que carrega.

**Stack:** a mesma de sempre (Python 3.12, FastAPI, SQLAlchemy 2.x, SQLite,
Pydantic v2, pytest + httpx) **+ `bcrypt`** (hash de senha, back-end) e
**Chart.js via CDN** (gráficos, front-end — nenhuma dependência Python
nova).

## Regras que sigo

- Python **3.12**; back-end em `backend/`, front em `frontend/`.
- Banco: **SQLite** via SQLAlchemy ORM. Nada de SQL cru fora do ORM.
- Dinheiro: continua `Numeric(10,2)` / `Decimal` / string com 2 casas no
  JSON (tipo `Money` já existente). **Soma de faturamento é feita em
  Python com `Decimal`, nunca em SQL** — SQLite não tem tipo decimal
  nativo, e arredondamento de dinheiro em ponto flutuante não é aceitável
  aqui. Contagem/soma de quantidade (inteiro) pode usar `func.sum` do SQL
  normalmente, sem esse problema.
- API sob `/api`. Erros no formato `{"detail": "<mensagem em português>"}`.
- Senha: nunca armazenada nem logada em texto puro — sempre hash `bcrypt`.
- Cookie de sessão: `HttpOnly` + `SameSite=Lax`. Sem a flag `Secure`
  (projeto roda em HTTP local) — ver `design-fase-3.md` seção 3.
- Sessão dura 8h e fica numa tabela própria — logout apaga a linha de
  verdade, não é só limpar o cookie.
- Só **atendente** e **admin** logam. "Cliente" não é um papel que loga
  nessa fase — pedido continua sendo criado por quem está logado (atendente
  ou admin), digitando o nome do cliente, igual já funciona hoje.
- Proteção client-side via `GET /api/me` no carregamento de cada página
  protegida (`/`, `/cardapio-admin.html`, `/relatorios.html`) — mas a
  proteção que importa de verdade é sempre a da API.
- Todo o trabalho dessa fase vai na branch `fase-3` (criada na Tarefa 1),
  um commit por passo de "Commit".
- Cada teste roda com: `cd backend && pytest`.
- Escopo travado: **só o que está neste plano**. Sem fluxo de status do
  pedido (cortado da Fase 2 — ver `design-fase-1.md`), sem cadastro/login
  de cliente, sem recuperação de senha, convite ou qualquer tela de gestão
  de usuários — o único usuário criado nessa fase é o admin padrão do seed.

---

## Estrutura de arquivos

```
backend/
  app/
    models.py            # Usuario, Sessao (tabelas novas)
    schemas.py            # LoginIn, UsuarioOut, ResumoRelatorio,
                           # FaturamentoDiarioItem, ProdutoMaisVendidoItem
    seed.py                # seed_usuarios + ADMIN_PADRAO_EMAIL/SENHA
    crud.py                 # listar_pedidos ganha filtros; +resumo_relatorio,
                             # faturamento_diario, produtos_mais_vendidos
    auth.py                  # NOVO — hash, sessão, usuario_logado, usuario_admin
    main.py                   # inclui routers auth/relatorios, chama seed_usuarios
    routers/
      auth.py                 # NOVO — POST /login, POST /logout, GET /me
      produtos.py               # ganha Depends(usuario_logado)/Depends(usuario_admin)
      pedidos.py                 # ganha Depends(usuario_logado) + busca/filtro
      relatorios.py                # NOVO — resumo, faturamento-diario, produtos-mais-vendidos
  requirements.txt                  # +bcrypt
  tests/
    conftest.py                      # seed_usuarios no fixture client; +client_admin/client_atendente
    test_usuarios.py                  # NOVO
    test_auth.py                       # NOVO
    test_produtos.py                    # client -> client_admin
    test_pedidos.py                      # client -> client_atendente, +testes de busca
    test_relatorios.py                    # NOVO
    test_frontend.py                       # +smoke tests login.html/relatorios.html
frontend/
  login.html                               # NOVO
  login.js                                  # NOVO
  relatorios.html                            # NOVO
  relatorios.js                               # NOVO
  app.js                                       # +verificarSessao, +aplicarUsuarioNoMenu
  admin.js                                      # idem
  index.html                                     # nav ganha link Relatórios + usuário/sair
  cardapio-admin.html                             # idem
  styles.css                                       # estilos de login, menu-usuario, cards-resumo
README.md                                             # credenciais admin, roadmap, estrutura
```

---

## Tarefa 1: Modelo de dados e seed do usuário admin

**Arquivos:**
- Modifico: `backend/app/models.py`
- Modifico: `backend/app/seed.py`
- Modifico: `backend/app/main.py`
- Modifico: `backend/requirements.txt`
- Modifico: `backend/tests/conftest.py`
- Modifico: `README.md`
- Teste: `backend/tests/test_usuarios.py`

**Interfaces:**
- Produz: `models.Usuario` (`id`, `nome`, `email`, `senha_hash`, `papel`,
  `criado_em`), `models.Sessao` (`token`, `usuario_id`, `criado_em`,
  `expira_em`), `seed.seed_usuarios(db) -> int`,
  `seed.ADMIN_PADRAO_EMAIL: str`, `seed.ADMIN_PADRAO_SENHA: str`.

- [ ] **Passo 1: Criar a branch de trabalho**

```bash
git checkout -b fase-3
```

- [ ] **Passo 2: Adicionar `bcrypt` e instalar**

Em `backend/requirements.txt`, acrescentar ao fim:

```
bcrypt==4.2.1
```

```bash
cd backend && pip install -r requirements.txt
```

- [ ] **Passo 3: Escrever o teste que falha**

Crio `backend/tests/test_usuarios.py`:

```python
from sqlalchemy.orm import Session

from app import models
from app.seed import ADMIN_PADRAO_EMAIL, ADMIN_PADRAO_SENHA, seed_usuarios


def test_seed_usuarios_cria_admin_padrao(db_session: Session) -> None:
    inseridos = seed_usuarios(db_session)
    assert inseridos == 1
    admin = db_session.query(models.Usuario).one()
    assert admin.email == ADMIN_PADRAO_EMAIL
    assert admin.papel == "admin"
    assert admin.senha_hash != ADMIN_PADRAO_SENHA  # nunca texto puro


def test_seed_usuarios_e_idempotente(db_session: Session) -> None:
    assert seed_usuarios(db_session) == 1
    assert seed_usuarios(db_session) == 0
    assert db_session.query(models.Usuario).count() == 1
```

- [ ] **Passo 4: Rodar e confirmar que falha**

```bash
cd backend && pytest tests/test_usuarios.py -v
```
Esperado: falha com `ImportError` (`seed_usuarios` ainda não existe).

- [ ] **Passo 5: Adicionar os modelos**

Em `backend/app/models.py`, acrescento ao fim do arquivo:

```python
class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Sessao(Base):
    __tablename__ = "sessao"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE")
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

(Os imports `Mapped`, `mapped_column`, `String`, `DateTime`, `ForeignKey`,
`datetime` já existem no topo do arquivo — nenhum import novo necessário.)

- [ ] **Passo 6: Adicionar o seed de usuários**

Em `backend/app/seed.py`, acrescento no topo (junto aos outros imports):

```python
import bcrypt
```

E ao fim do arquivo:

```python
ADMIN_PADRAO_EMAIL = "admin@hamburgueria.com"
ADMIN_PADRAO_SENHA = "admin123"  # credencial de demonstracao, ver README


def seed_usuarios(db: Session) -> int:
    ja_existem = db.scalar(select(func.count()).select_from(models.Usuario))
    if ja_existem:
        return 0
    senha_hash = bcrypt.hashpw(
        ADMIN_PADRAO_SENHA.encode(), bcrypt.gensalt()
    ).decode()
    admin = models.Usuario(
        nome="Administrador",
        email=ADMIN_PADRAO_EMAIL,
        senha_hash=senha_hash,
        papel="admin",
    )
    db.add(admin)
    db.commit()
    return 1
```

- [ ] **Passo 7: Rodar e confirmar que passa**

```bash
cd backend && pytest tests/test_usuarios.py -v
```
Esperado: `2 passed`.

- [ ] **Passo 8: Ligar o seed no servidor real**

Em `backend/app/main.py`, dentro de `inicializar_banco()`:

```python
def inicializar_banco() -> None:
    """Cria as tabelas e popula o cardápio. Só roda no startup do servidor real."""
    Base.metadata.create_all(engine)
    from app.seed import seed_cardapio, seed_usuarios

    db = SessionLocal()
    try:
        seed_cardapio(db)
        seed_usuarios(db)
    finally:
        db.close()
```

- [ ] **Passo 9: Ligar o seed no fixture de teste**

Em `backend/tests/conftest.py`, dentro do fixture `client`:

```python
@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app(inicializar=False)
    from app.seed import seed_cardapio, seed_usuarios

    seed_cardapio(db_session)
    seed_usuarios(db_session)

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

- [ ] **Passo 10: Rodar a suíte inteira**

```bash
cd backend && pytest -v
```
Esperado: os 60 testes anteriores continuam passando (nenhuma rota mudou
ainda), mais os 2 novos de `test_usuarios.py` — **62 passed**. Como
`Usuario`/`Sessao` são tabelas novas (não colunas em tabela existente),
`Base.metadata.create_all` cria elas sozinho num `app.db` já existente —
**não precisa apagar o banco dessa vez**.

- [ ] **Passo 11: Documentar a credencial padrão no README**

Em `README.md`, logo depois do bloco "Atualizando de uma fase anterior?",
acrescento:

```markdown
> **Login padrão (Fase 3):** e-mail `admin@hamburgueria.com`, senha
> `admin123` — criado automaticamente na primeira execução. É só uma
> credencial de demonstração para a entrega da faculdade.
```

- [ ] **Passo 12: Commit**

```bash
git add backend/app/models.py backend/app/seed.py backend/app/main.py backend/requirements.txt backend/tests/conftest.py backend/tests/test_usuarios.py README.md
git commit -m "feat: modelo de usuario/sessao e seed do admin padrao"
```

---

## Tarefa 2: Backend de autenticação (login, logout, sessão atual)

**Arquivos:**
- Cria: `backend/app/auth.py`
- Cria: `backend/app/routers/auth.py`
- Modifico: `backend/app/schemas.py`
- Modifico: `backend/app/main.py`
- Teste: `backend/tests/test_auth.py`

**Interfaces:**
- Consome: `models.Usuario`, `models.Sessao`, `seed.ADMIN_PADRAO_EMAIL`,
  `seed.ADMIN_PADRAO_SENHA` (já existem da Tarefa 1).
- Produz: `auth.NOME_COOKIE: str`, `auth.DURACAO_SESSAO: timedelta`,
  `auth.autenticar(db, email, senha) -> Usuario | None`,
  `auth.criar_sessao(db, usuario_id) -> str`,
  `auth.excluir_sessao(db, token) -> None`,
  `auth.usuario_logado` e `auth.usuario_admin` (dependências FastAPI,
  usadas pelas próximas tarefas), rotas `POST /api/login`,
  `POST /api/logout`, `GET /api/me`.

- [ ] **Passo 1: Escrever o teste que falha**

Crio `backend/tests/test_auth.py`:

```python
from fastapi.testclient import TestClient

from app.seed import ADMIN_PADRAO_EMAIL, ADMIN_PADRAO_SENHA


def test_login_valido(client: TestClient) -> None:
    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["email"] == ADMIN_PADRAO_EMAIL
    assert corpo["papel"] == "admin"
    assert "sessao_token" in resp.cookies


def test_login_senha_errada_401(client: TestClient) -> None:
    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": "senha-errada"},
    )
    assert resp.status_code == 401


def test_login_email_inexistente_401(client: TestClient) -> None:
    resp = client.post(
        "/api/login", json={"email": "ninguem@teste.com", "senha": "qualquer"}
    )
    assert resp.status_code == 401


def test_me_sem_sessao_401(client: TestClient) -> None:
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_me_com_sessao_retorna_usuario(client: TestClient) -> None:
    client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    resp = client.get("/api/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == ADMIN_PADRAO_EMAIL


def test_logout_limpa_sessao(client: TestClient) -> None:
    client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    resp = client.post("/api/logout")
    assert resp.status_code == 204
    resp2 = client.get("/api/me")
    assert resp2.status_code == 401
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
cd backend && pytest tests/test_auth.py -v
```
Esperado: `404` em tudo (rotas ainda não existem).

- [ ] **Passo 3: Schemas de login**

Em `backend/app/schemas.py`, acrescento:

```python
class LoginIn(BaseModel):
    email: str = Field(min_length=1, max_length=120)
    senha: str = Field(min_length=1)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    papel: str
```

- [ ] **Passo 4: Criar `backend/app/auth.py`**

```python
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

NOME_COOKIE = "sessao_token"
DURACAO_SESSAO = timedelta(hours=8)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def autenticar(db: Session, email: str, senha: str) -> models.Usuario | None:
    usuario = db.scalar(select(models.Usuario).where(models.Usuario.email == email))
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario


def criar_sessao(db: Session, usuario_id: int) -> str:
    token = secrets.token_hex(32)
    agora = datetime.now(timezone.utc)
    sessao = models.Sessao(
        token=token,
        usuario_id=usuario_id,
        criado_em=agora,
        expira_em=agora + DURACAO_SESSAO,
    )
    db.add(sessao)
    db.commit()
    return token


def excluir_sessao(db: Session, token: str) -> None:
    sessao = db.get(models.Sessao, token)
    if sessao is not None:
        db.delete(sessao)
        db.commit()


def usuario_logado(
    sessao_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """Dependencia FastAPI: qualquer papel logado. O nome do parametro
    `sessao_token` precisa bater com NOME_COOKIE -- e como o FastAPI le
    cookie pelo nome do parametro."""
    if sessao_token is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    sessao = db.get(models.Sessao, sessao_token)
    if sessao is None or sessao.expira_em < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    usuario = db.get(models.Usuario, sessao.usuario_id)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return usuario


def usuario_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    if usuario.papel != "admin":
        raise HTTPException(
            status_code=403, detail="Acesso restrito a administradores."
        )
    return usuario
```

- [ ] **Passo 5: Criar `backend/app/routers/auth.py`**

```python
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api", tags=["autenticacao"])


@router.post("/login", response_model=schemas.UsuarioOut)
def login(
    dados: schemas.LoginIn, response: Response, db: Session = Depends(get_db)
):
    usuario = auth.autenticar(db, dados.email, dados.senha)
    if usuario is None:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    token = auth.criar_sessao(db, usuario.id)
    response.set_cookie(
        key=auth.NOME_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=int(auth.DURACAO_SESSAO.total_seconds()),
    )
    return usuario


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    sessao_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if sessao_token is not None:
        auth.excluir_sessao(db, sessao_token)
    response.delete_cookie(auth.NOME_COOKIE)


@router.get("/me", response_model=schemas.UsuarioOut)
def me(usuario: models.Usuario = Depends(auth.usuario_logado)):
    return usuario
```

- [ ] **Passo 6: Registrar o router em `main.py`**

Em `backend/app/main.py`, dentro de `create_app`, logo depois do
`health`:

```python
    from app.routers import auth

    app.include_router(auth.router)

    from app.routers import produtos

    app.include_router(produtos.router)
```

(mantenho a ordem dos outros `include_router` como já estava, só acrescento
o de `auth` antes.)

- [ ] **Passo 7: Rodar e confirmar que passa**

```bash
cd backend && pytest -v
```
Esperado: **68 passed** (62 anteriores + 6 de `test_auth.py`).

- [ ] **Passo 8: Commit**

```bash
git add backend/app/auth.py backend/app/routers/auth.py backend/app/schemas.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: autenticacao por sessao (login, logout, GET /api/me)"
```

---

## Tarefa 3: Proteger Produtos e Pedidos, migrar os testes existentes

**Arquivos:**
- Modifico: `backend/app/routers/produtos.py`
- Modifico: `backend/app/routers/pedidos.py`
- Modifico: `backend/tests/conftest.py`
- Modifico: `backend/tests/test_produtos.py`
- Modifico: `backend/tests/test_pedidos.py`

**Interfaces:**
- Consome: `auth.usuario_logado`, `auth.usuario_admin` (Tarefa 2).
- Produz: fixtures de teste `client_admin` e `client_atendente`
  (`backend/tests/conftest.py`), usadas por esta tarefa e por todas as
  seguintes.

- [ ] **Passo 1: Adicionar os fixtures autenticados**

Em `backend/tests/conftest.py`, acrescento `import bcrypt` e
`from app import models` no topo, e os dois fixtures novos ao fim do
arquivo:

```python
import bcrypt
```
(junto aos outros imports do topo)

```python
from app import models
```
(junto a `from app.database import Base, get_db`)

```python
@pytest.fixture
def client_admin(client: TestClient) -> TestClient:
    from app.seed import ADMIN_PADRAO_EMAIL, ADMIN_PADRAO_SENHA

    resp = client.post(
        "/api/login",
        json={"email": ADMIN_PADRAO_EMAIL, "senha": ADMIN_PADRAO_SENHA},
    )
    assert resp.status_code == 200
    return client


@pytest.fixture
def client_atendente(client: TestClient, db_session: Session) -> TestClient:
    senha_hash = bcrypt.hashpw(b"teste123", bcrypt.gensalt()).decode()
    usuario = models.Usuario(
        nome="Atendente Teste",
        email="atendente@teste.com",
        senha_hash=senha_hash,
        papel="atendente",
    )
    db_session.add(usuario)
    db_session.commit()

    resp = client.post(
        "/api/login", json={"email": "atendente@teste.com", "senha": "teste123"}
    )
    assert resp.status_code == 200
    return client
```

- [ ] **Passo 2: Proteger `backend/app/routers/produtos.py`**

Troco o import do topo:

```python
from app import auth, crud, models, schemas
```

E acrescento `_usuario: models.Usuario = Depends(auth.usuario_logado)` nos
dois `GET` (`listar`, `detalhar`) e `_usuario: models.Usuario =
Depends(auth.usuario_admin)` nos quatro de escrita (`criar`, `atualizar`,
`excluir`, `enviar_imagem`). Arquivo completo:

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import auth, crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


@router.get("", response_model=list[schemas.ProdutoOut])
def listar(
    incluir_indisponiveis: bool = False,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
) -> list[models.Produto]:
    return crud.listar_produtos(db, incluir_indisponiveis)


@router.get("/{produto_id}", response_model=schemas.ProdutoOut)
def detalhar(
    produto_id: int,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    produto = crud.obter_produto(db, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@router.post(
    "", response_model=schemas.ProdutoOut, status_code=status.HTTP_201_CREATED
)
def criar(
    dados: schemas.ProdutoIn,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    try:
        produto = crud.criar_produto(db, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    return produto


@router.put("/{produto_id}", response_model=schemas.ProdutoOut)
def atualizar(
    produto_id: int,
    dados: schemas.ProdutoIn,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    try:
        produto = crud.atualizar_produto(db, produto_id, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    produto_id: int,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    try:
        encontrou = crud.excluir_produto(db, produto_id)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    if not encontrou:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")


@router.post("/{produto_id}/imagem", response_model=schemas.ProdutoOut)
async def enviar_imagem(
    produto_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_admin),
):
    try:
        produto = await crud.salvar_imagem_produto(db, produto_id, arquivo)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto
```

- [ ] **Passo 3: Proteger `backend/app/routers/pedidos.py`**

Arquivo completo:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, models, schemas, serializers
from app.database import get_db

router = APIRouter(prefix="/api/pedidos", tags=["pedidos"])


@router.post(
    "", response_model=schemas.PedidoOut, status_code=status.HTTP_201_CREATED
)
def criar(
    dados: schemas.PedidoIn,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    try:
        pedido = crud.criar_pedido(db, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    return serializers.pedido_para_out(pedido)


@router.get("", response_model=list[schemas.PedidoResumo])
def listar(
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    return [
        serializers.pedido_para_resumo(p) for p in crud.listar_pedidos(db)
    ]


@router.get("/{pedido_id}", response_model=schemas.PedidoOut)
def detalhar(
    pedido_id: int,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    pedido = crud.obter_pedido(db, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return serializers.pedido_para_out(pedido)


@router.put("/{pedido_id}", response_model=schemas.PedidoOut)
def atualizar(
    pedido_id: int,
    dados: schemas.PedidoIn,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    try:
        pedido = crud.atualizar_pedido(db, pedido_id, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return serializers.pedido_para_out(pedido)


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(
    pedido_id: int,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    if not crud.excluir_pedido(db, pedido_id):
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
```

(O parâmetro `listar` aqui ainda não tem busca/filtro — isso entra na
Tarefa 5, junto com os relatórios, pra não misturar os dois assuntos.)

- [ ] **Passo 4: Rodar a suíte — confirmar que os testes antigos quebram**

```bash
cd backend && pytest -v
```
Esperado: vários `401` em `test_produtos.py` e `test_pedidos.py` — é o
esperado, confirma que a proteção está funcionando. É isso que os próximos
dois passos corrigem.

- [ ] **Passo 5: Migrar `test_produtos.py` para `client_admin`**

Em `backend/tests/test_produtos.py`, troco **toda ocorrência do
identificador `client`** por `client_admin` — tanto nos parâmetros de
função quanto nos usos no corpo. É uma renomeação mecânica por palavra
inteira (não mexe em `db_session`, `uploads_tmp` nem em nenhum outro
nome). Exemplo do início do arquivo, antes:

```python
def test_get_produtos_retorna_seed(client: TestClient) -> None:
    resp = client.get("/api/produtos")
```

Depois:

```python
def test_get_produtos_retorna_seed(client_admin: TestClient) -> None:
    resp = client_admin.get("/api/produtos")
```

Aplico o mesmo padrão nas ~39 ocorrências do arquivo inteiro. Ao final,
confiro que sobrou zero `client` solto:

```bash
grep -n '\bclient\b' backend/tests/test_produtos.py
```
Esperado: nenhuma linha (só deve restar `client_admin`, `db_session`,
`uploads_tmp`, `TestClient`).

Acrescento também um teste novo, provando que atendente não consegue
mexer no cardápio, ao fim do arquivo:

```python
def test_criar_produto_sem_permissao_403(client_atendente: TestClient) -> None:
    resp = client_atendente.post("/api/produtos", json=PRODUTO_NOVO)
    assert resp.status_code == 403


def test_listar_produtos_sem_sessao_401(client: TestClient) -> None:
    resp = client.get("/api/produtos")
    assert resp.status_code == 401
```

- [ ] **Passo 6: Migrar `test_pedidos.py` para `client_atendente`**

Mesmo processo: troco toda ocorrência de `client` por `client_atendente`
em `backend/tests/test_pedidos.py` (~36 ocorrências). Confiro:

```bash
grep -n '\bclient\b' backend/tests/test_pedidos.py
```
Esperado: nenhuma linha.

Acrescento ao fim do arquivo:

```python
def test_criar_pedido_sem_sessao_401(client: TestClient) -> None:
    resp = client.post("/api/pedidos", json=PEDIDO_VALIDO)
    assert resp.status_code == 401
```

- [ ] **Passo 7: Rodar a suíte inteira**

```bash
cd backend && pytest -v
```
Esperado: **71 passed** (68 anteriores + 3 testes novos de permissão —
`test_criar_produto_sem_permissao_403`,
`test_listar_produtos_sem_sessao_401`,
`test_criar_pedido_sem_sessao_401`).

- [ ] **Passo 8: Commit**

```bash
git add backend/app/routers/produtos.py backend/app/routers/pedidos.py backend/tests/conftest.py backend/tests/test_produtos.py backend/tests/test_pedidos.py
git commit -m "feat: protege rotas de produtos e pedidos com login"
```

---

## Tarefa 4: Frontend de login

**Arquivos:**
- Cria: `frontend/login.html`
- Cria: `frontend/login.js`
- Modifico: `frontend/app.js`
- Modifico: `frontend/admin.js`
- Modifico: `frontend/index.html`
- Modifico: `frontend/cardapio-admin.html`
- Modifico: `frontend/styles.css`
- Teste: `backend/tests/test_frontend.py`

**Interfaces:**
- Consome: `POST /api/login`, `POST /api/logout`, `GET /api/me` (Tarefa 2).
- Produz: `verificarSessao(papelExigido?)` e `aplicarUsuarioNoMenu(usuario)`
  — funções JS duplicadas em `app.js`/`admin.js` (e, na Tarefa 6, em
  `relatorios.js`), seguindo o padrão já usado no projeto pra `esc()`,
  `brl()`, `initMenu()`.

- [ ] **Passo 1: Criar `frontend/login.html`**

```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hamburgueria — Entrar</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Work+Sans:wght@400;500;600&display=swap">
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header>
    <h1>🍔 Hamburgueria</h1>
  </header>

  <div id="aviso" class="aviso" hidden></div>

  <main class="login-main">
    <section class="login-box">
      <h2>Entrar</h2>
      <form id="form-login">
        <label>E-mail
          <input type="email" id="email" required autofocus />
        </label>
        <label>Senha
          <input type="password" id="senha" required />
        </label>
        <div class="acoes">
          <button type="submit">Entrar</button>
        </div>
      </form>
    </section>
  </main>

  <script src="login.js"></script>
</body>
</html>
```

- [ ] **Passo 2: Criar `frontend/login.js`**

```javascript
"use strict";

const API = "/api";
const $ = (sel) => document.querySelector(sel);

function aviso(msg, tipo) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso " + tipo;
  el.hidden = false;
}

$("#form-login").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const email = $("#email").value.trim();
  const senha = $("#senha").value;
  try {
    const resp = await fetch(`${API}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    if (!resp.ok) {
      const corpo = await resp.json().catch(() => ({}));
      throw new Error(corpo.detail || "E-mail ou senha inválidos.");
    }
    window.location.href = "/";
  } catch (e) {
    aviso(e.message, "erro");
  }
});
```

- [ ] **Passo 3: Estilos do login em `frontend/styles.css`**

Acrescento ao fim do arquivo:

```css
.login-main {
  display: flex;
  justify-content: center;
  padding: 48px 16px;
}
.login-box {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 28px;
  width: 100%;
  max-width: 360px;
}
.menu-usuario {
  border-top: 1px solid var(--line);
  margin-top: 6px;
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
#usuario-nome {
  font-size: 0.85rem;
  color: var(--muted);
  padding: 0 12px;
}
```

- [ ] **Passo 4: Smoke test da página**

Em `backend/tests/test_frontend.py`, acrescento:

```python
def test_login_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/login.html")
    assert resp.status_code == 200
    assert "Entrar" in resp.text
    assert "login.js" in resp.text
```

- [ ] **Passo 5: Rodar e confirmar que passa**

```bash
cd backend && pytest tests/test_frontend.py -v
```

- [ ] **Passo 6: Atualizar o menu em `frontend/index.html`**

Troco o `<nav class="hamb-menu">` por:

```html
<nav class="hamb-menu" id="menu-nav" hidden>
  <a href="/" class="active">Pedidos</a>
  <a href="/cardapio-admin.html" id="link-cardapio">Gerenciar Cardápio</a>
  <a href="/relatorios.html" id="link-relatorios">Relatórios</a>
  <div class="menu-usuario">
    <span id="usuario-nome"></span>
    <button type="button" id="btn-sair" class="secundario">Sair</button>
  </div>
</nav>
```

- [ ] **Passo 7: Atualizar o menu em `frontend/cardapio-admin.html`**

```html
<nav class="hamb-menu" id="menu-nav" hidden>
  <a href="/">Pedidos</a>
  <a href="/cardapio-admin.html" class="active">Gerenciar Cardápio</a>
  <a href="/relatorios.html">Relatórios</a>
  <div class="menu-usuario">
    <span id="usuario-nome"></span>
    <button type="button" id="btn-sair" class="secundario">Sair</button>
  </div>
</nav>
```

(`cardapio-admin.html` e, na Tarefa 6, `relatorios.html` são sempre
admin-only — quem chegou até essas páginas já é admin, então não preciso
esconder nenhum link nelas. Só em `index.html`, que atendente também
acessa, os links de Cardápio/Relatórios precisam sumir pra quem não é
admin.)

- [ ] **Passo 8: Checagem de sessão em `frontend/app.js`**

Acrescento, logo depois dos helpers `esc`/`initMenu` já existentes:

```javascript
async function verificarSessao(papelExigido) {
  const resp = await fetch(`${API}/me`);
  if (resp.status === 401) {
    window.location.href = "/login.html";
    return null;
  }
  const usuario = await resp.json();
  if (papelExigido && usuario.papel !== papelExigido) {
    window.location.href = "/";
    return null;
  }
  return usuario;
}

function aplicarUsuarioNoMenu(usuario) {
  $("#usuario-nome").textContent = usuario.nome;
  const linkCardapio = $("#link-cardapio");
  const linkRelatorios = $("#link-relatorios");
  if (linkCardapio) linkCardapio.hidden = usuario.papel !== "admin";
  if (linkRelatorios) linkRelatorios.hidden = usuario.papel !== "admin";
  $("#btn-sair").addEventListener("click", async () => {
    await fetch(`${API}/logout`, { method: "POST" });
    window.location.href = "/login.html";
  });
}
```

E troco a IIFE `iniciar()` no fim do arquivo:

```javascript
(async function iniciar() {
  const usuario = await verificarSessao();
  if (!usuario) return;
  aplicarUsuarioNoMenu(usuario);
  try {
    await carregarCardapio();
    await carregarPedidos();
    renderCarrinho();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
```

- [ ] **Passo 9: Checagem de sessão em `frontend/admin.js`**

Acrescento as mesmas duas funções `verificarSessao`/`aplicarUsuarioNoMenu`
(idêntico ao Passo 8 — sem `linkCardapio`/`linkRelatorios` pra esconder,
já que quem chega aqui já é admin). E troco a IIFE `iniciar()`:

```javascript
(async function iniciar() {
  const usuario = await verificarSessao("admin");
  if (!usuario) return;
  aplicarUsuarioNoMenu(usuario);
  try {
    await carregarProdutos();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
```

- [ ] **Passo 10: Rodar a suíte inteira**

```bash
cd backend && pytest -v
```
Esperado: ainda **72 passed** (nenhuma rota de API mudou nessa tarefa, só
front-end estático — o teste novo do Passo 4/5 já estava contado).

- [ ] **Passo 11: Testar manualmente**

```bash
cd backend && rm -f app.db && uvicorn app.main:app --reload
```

Abro `http://localhost:8000/` no navegador — devo ser redirecionado pra
`/login.html`. Entro com `admin@hamburgueria.com` / `admin123` — devo cair
em `/`, ver meu nome no menu e os três links (Pedidos, Gerenciar Cardápio,
Relatórios — esse último ainda dá 404 até a Tarefa 6). Clico em "Sair" —
devo voltar pro login.

- [ ] **Passo 12: Commit**

```bash
git add frontend/login.html frontend/login.js frontend/app.js frontend/admin.js frontend/index.html frontend/cardapio-admin.html frontend/styles.css backend/tests/test_frontend.py
git commit -m "feat: tela de login e protecao client-side das paginas"
```

---

## Tarefa 5: Backend de relatórios

**Arquivos:**
- Cria: `backend/app/routers/relatorios.py`
- Modifico: `backend/app/crud.py`
- Modifico: `backend/app/schemas.py`
- Modifico: `backend/app/routers/pedidos.py`
- Modifico: `backend/app/main.py`
- Teste: `backend/tests/test_relatorios.py`

**Interfaces:**
- Consome: `auth.usuario_admin` (Tarefa 2).
- Produz: `crud.listar_pedidos(db, cliente_nome=None, data_inicio=None,
  data_fim=None)` (assinatura estendida, retrocompatível),
  `crud.resumo_relatorio`, `crud.faturamento_diario`,
  `crud.produtos_mais_vendidos`, rotas `GET /api/relatorios/resumo`,
  `GET /api/relatorios/faturamento-diario`,
  `GET /api/relatorios/produtos-mais-vendidos`, e busca/filtro em
  `GET /api/pedidos`.

- [ ] **Passo 1: Escrever o teste que falha**

Crio `backend/tests/test_relatorios.py`:

```python
from fastapi.testclient import TestClient

PEDIDO_A = {
    "cliente_nome": "Bruno",
    "itens": [{"produto_id": 1, "quantidade": 2}],  # X-Salada 18.00 x2 = 36.00
}
PEDIDO_B = {
    "cliente_nome": "Carla",
    "itens": [{"produto_id": 5, "quantidade": 3}],  # Batata Frita 12.00 x3 = 36.00
}


def test_relatorios_bloqueado_pra_atendente(client_atendente: TestClient) -> None:
    resp = client_atendente.get("/api/relatorios/resumo")
    assert resp.status_code == 403


def test_resumo_relatorio(client_admin: TestClient) -> None:
    client_admin.post("/api/pedidos", json=PEDIDO_A)
    client_admin.post("/api/pedidos", json=PEDIDO_B)

    resp = client_admin.get("/api/relatorios/resumo")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["total_pedidos"] == 2
    assert corpo["faturamento_total"] == "72.00"
    assert corpo["ticket_medio"] == "36.00"


def test_resumo_relatorio_sem_pedidos(client_admin: TestClient) -> None:
    resp = client_admin.get("/api/relatorios/resumo")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["total_pedidos"] == 0
    assert corpo["ticket_medio"] == "0.00"


def test_produtos_mais_vendidos(client_admin: TestClient) -> None:
    client_admin.post("/api/pedidos", json=PEDIDO_A)
    resp = client_admin.get("/api/relatorios/produtos-mais-vendidos")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo[0]["produto_nome"] == "X-Salada"
    assert corpo[0]["quantidade_total"] == 2


def test_faturamento_diario(client_admin: TestClient) -> None:
    client_admin.post("/api/pedidos", json=PEDIDO_A)
    resp = client_admin.get("/api/relatorios/faturamento-diario")
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 1
    assert corpo[0]["total"] == "36.00"


def test_buscar_pedidos_por_cliente(client_atendente: TestClient) -> None:
    client_atendente.post("/api/pedidos", json=PEDIDO_A)
    client_atendente.post("/api/pedidos", json=PEDIDO_B)

    resp = client_atendente.get("/api/pedidos", params={"cliente_nome": "bru"})
    assert resp.status_code == 200
    corpo = resp.json()
    assert len(corpo) == 1
    assert corpo[0]["cliente_nome"] == "Bruno"
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
cd backend && pytest tests/test_relatorios.py -v
```
Esperado: `404` nos endpoints de relatório.

- [ ] **Passo 3: Schemas de relatório**

Em `backend/app/schemas.py`, acrescento:

```python
class ResumoRelatorio(BaseModel):
    total_pedidos: int
    faturamento_total: Money
    ticket_medio: Money


class FaturamentoDiarioItem(BaseModel):
    data: str
    total: Money


class ProdutoMaisVendidoItem(BaseModel):
    produto_nome: str
    quantidade_total: int
```

- [ ] **Passo 4: Funções de agregação em `crud.py`**

No topo de `backend/app/crud.py`, troco o import de `decimal`:

```python
from datetime import date, datetime
from decimal import Decimal
```

E troco a assinatura de `listar_pedidos` (função já existente):

```python
def listar_pedidos(
    db: Session,
    cliente_nome: str | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> list[models.Pedido]:
    stmt = select(models.Pedido).order_by(
        models.Pedido.criado_em.desc(), models.Pedido.id.desc()
    )
    if cliente_nome:
        stmt = stmt.where(models.Pedido.cliente_nome.ilike(f"%{cliente_nome}%"))
    if data_inicio:
        stmt = stmt.where(models.Pedido.criado_em >= data_inicio)
    if data_fim:
        stmt = stmt.where(models.Pedido.criado_em <= data_fim)
    return list(db.scalars(stmt))
```

(Retrocompatível: todo mundo que já chama `crud.listar_pedidos(db)` sem os
novos argumentos continua funcionando igual.)

E acrescento ao fim do arquivo:

```python
def _item_subtotal(item: models.ItemPedido) -> Decimal:
    return Decimal(item.preco_unitario) * item.quantidade


def resumo_relatorio(
    db: Session, data_inicio: datetime, data_fim: datetime
) -> tuple[int, Decimal, Decimal]:
    pedidos = listar_pedidos(db, data_inicio=data_inicio, data_fim=data_fim)
    total_pedidos = len(pedidos)
    faturamento_total = sum(
        (_item_subtotal(item) for pedido in pedidos for item in pedido.itens),
        Decimal("0"),
    )
    ticket_medio = (
        faturamento_total / total_pedidos if total_pedidos else Decimal("0")
    )
    return total_pedidos, faturamento_total, ticket_medio


def faturamento_diario(
    db: Session, data_inicio: datetime, data_fim: datetime
) -> list[tuple[date, Decimal]]:
    pedidos = listar_pedidos(db, data_inicio=data_inicio, data_fim=data_fim)
    totais_por_dia: dict[date, Decimal] = {}
    for pedido in pedidos:
        dia = pedido.criado_em.date()
        subtotal_pedido = sum(
            (_item_subtotal(item) for item in pedido.itens), Decimal("0")
        )
        totais_por_dia[dia] = totais_por_dia.get(dia, Decimal("0")) + subtotal_pedido
    return sorted(totais_por_dia.items())


def produtos_mais_vendidos(
    db: Session, data_inicio: datetime, data_fim: datetime, limite: int
) -> list[tuple[str, int]]:
    stmt = (
        select(
            models.ItemPedido.produto_nome,
            func.sum(models.ItemPedido.quantidade).label("total"),
        )
        .join(models.Pedido, models.Pedido.id == models.ItemPedido.pedido_id)
        .where(models.Pedido.criado_em >= data_inicio)
        .where(models.Pedido.criado_em <= data_fim)
        .group_by(models.ItemPedido.produto_nome)
        .order_by(func.sum(models.ItemPedido.quantidade).desc())
        .limit(limite)
    )
    return list(db.execute(stmt).all())
```

(`resumo_relatorio` e `faturamento_diario` somam dinheiro em **Python com
`Decimal`**, reaproveitando o mesmo cálculo de subtotal que
`serializers.py` já usa — nunca `SUM` de dinheiro em SQL, por causa da
imprecisão de ponto flutuante do SQLite. `produtos_mais_vendidos` soma
**quantidade**, que é inteiro — aí sim uso `func.sum` do SQL, sem
problema.)

- [ ] **Passo 5: Criar `backend/app/routers/relatorios.py`**

```python
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
```

- [ ] **Passo 6: Busca/filtro em `GET /api/pedidos`**

Em `backend/app/routers/pedidos.py`, troco a função `listar` e acrescento
o import de `datetime`:

```python
from datetime import datetime
```
(junto aos outros imports do topo)

```python
@router.get("", response_model=list[schemas.PedidoResumo])
def listar(
    cliente_nome: str | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    db: Session = Depends(get_db),
    _usuario: models.Usuario = Depends(auth.usuario_logado),
):
    pedidos = crud.listar_pedidos(db, cliente_nome, data_inicio, data_fim)
    return [serializers.pedido_para_resumo(p) for p in pedidos]
```

- [ ] **Passo 7: Registrar o router em `main.py`**

Em `backend/app/main.py`, dentro de `create_app`, depois do
`include_router(pedidos.router)`:

```python
    from app.routers import relatorios

    app.include_router(relatorios.router)
```

- [ ] **Passo 8: Rodar a suíte inteira**

```bash
cd backend && pytest -v
```
Esperado: **78 passed** (72 anteriores + 6 de `test_relatorios.py`).

- [ ] **Passo 9: Commit**

```bash
git add backend/app/routers/relatorios.py backend/app/crud.py backend/app/schemas.py backend/app/routers/pedidos.py backend/app/main.py backend/tests/test_relatorios.py
git commit -m "feat: endpoints de relatorios e busca/filtro de pedidos"
```

---

## Tarefa 6: Frontend de relatórios

**Arquivos:**
- Cria: `frontend/relatorios.html`
- Cria: `frontend/relatorios.js`
- Modifico: `frontend/styles.css`
- Modifico: `README.md`
- Teste: `backend/tests/test_frontend.py`

**Interfaces:**
- Consome: `GET /api/relatorios/resumo`, `GET /api/relatorios/faturamento-diario`,
  `GET /api/relatorios/produtos-mais-vendidos`, `GET /api/pedidos` com
  filtros (Tarefa 5); `verificarSessao`/`aplicarUsuarioNoMenu` (Tarefa 4,
  duplicadas aqui).

- [ ] **Passo 1: Criar `frontend/relatorios.html`**

```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hamburgueria — Relatórios</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Work+Sans:wght@400;500;600&display=swap">
  <link rel="stylesheet" href="styles.css" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
</head>
<body>
  <header>
    <h1>🍔 Hamburgueria — Relatórios</h1>
    <button class="hamb-btn" id="btn-menu" aria-label="Abrir menu" aria-expanded="false">☰</button>
    <nav class="hamb-menu" id="menu-nav" hidden>
      <a href="/">Pedidos</a>
      <a href="/cardapio-admin.html">Gerenciar Cardápio</a>
      <a href="/relatorios.html" class="active">Relatórios</a>
      <div class="menu-usuario">
        <span id="usuario-nome"></span>
        <button type="button" id="btn-sair" class="secundario">Sair</button>
      </div>
    </nav>
  </header>

  <div id="aviso" class="aviso" hidden></div>

  <main>
    <section id="secao-filtro">
      <h2>Relatórios</h2>
      <form id="form-filtro">
        <label>De
          <input type="date" id="data_inicio" />
        </label>
        <label>Até
          <input type="date" id="data_fim" />
        </label>
        <button type="submit">Filtrar</button>
      </form>
    </section>

    <section id="secao-resumo">
      <div class="cards-resumo">
        <div class="card-resumo">
          <small>Total de pedidos</small>
          <strong id="resumo-total-pedidos">—</strong>
        </div>
        <div class="card-resumo">
          <small>Faturamento</small>
          <strong id="resumo-faturamento">—</strong>
        </div>
        <div class="card-resumo">
          <small>Ticket médio</small>
          <strong id="resumo-ticket-medio">—</strong>
        </div>
      </div>
    </section>

    <section id="secao-graficos">
      <h2>Faturamento por dia</h2>
      <canvas id="grafico-faturamento"></canvas>

      <h2>Produtos mais vendidos</h2>
      <canvas id="grafico-produtos"></canvas>
    </section>

    <section id="secao-busca-pedidos">
      <h2>Buscar pedidos</h2>
      <form id="form-busca">
        <label>Cliente
          <input type="text" id="busca-cliente" placeholder="Nome do cliente" />
        </label>
        <button type="submit">Buscar</button>
      </form>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Cliente</th><th>Itens</th><th>Total</th>
            <th>Status</th><th>Criado em</th>
          </tr>
        </thead>
        <tbody id="lista-pedidos-busca"></tbody>
      </table>
      <p id="busca-vazia" hidden>Nenhum pedido encontrado.</p>
    </section>
  </main>

  <script src="relatorios.js"></script>
</body>
</html>
```

- [ ] **Passo 2: Criar `frontend/relatorios.js`**

```javascript
"use strict";

const API = "/api";
let graficoFaturamento = null;
let graficoProdutos = null;

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

function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function initMenu() {
  const btn = $("#btn-menu");
  const menu = $("#menu-nav");
  btn.addEventListener("click", () => {
    const vaiAbrir = menu.hidden;
    menu.hidden = !vaiAbrir;
    btn.setAttribute("aria-expanded", String(vaiAbrir));
  });
  document.addEventListener("click", (e) => {
    if (!menu.hidden && !menu.contains(e.target) && e.target !== btn) {
      menu.hidden = true;
      btn.setAttribute("aria-expanded", "false");
    }
  });
}

async function verificarSessao(papelExigido) {
  const resp = await fetch(`${API}/me`);
  if (resp.status === 401) {
    window.location.href = "/login.html";
    return null;
  }
  const usuario = await resp.json();
  if (papelExigido && usuario.papel !== papelExigido) {
    window.location.href = "/";
    return null;
  }
  return usuario;
}

function aplicarUsuarioNoMenu(usuario) {
  $("#usuario-nome").textContent = usuario.nome;
  $("#btn-sair").addEventListener("click", async () => {
    await fetch(`${API}/logout`, { method: "POST" });
    window.location.href = "/login.html";
  });
}

function periodoSelecionado() {
  const inicio = $("#data_inicio").value;
  const fim = $("#data_fim").value;
  const params = new URLSearchParams();
  if (inicio) params.set("data_inicio", `${inicio}T00:00:00Z`);
  if (fim) params.set("data_fim", `${fim}T23:59:59Z`);
  return params;
}

async function carregarResumo() {
  const resp = await fetch(`${API}/relatorios/resumo?${periodoSelecionado()}`);
  const corpo = await resp.json();
  $("#resumo-total-pedidos").textContent = corpo.total_pedidos;
  $("#resumo-faturamento").textContent = brl(corpo.faturamento_total);
  $("#resumo-ticket-medio").textContent = brl(corpo.ticket_medio);
}

async function carregarGraficoFaturamento() {
  const resp = await fetch(
    `${API}/relatorios/faturamento-diario?${periodoSelecionado()}`
  );
  const dados = await resp.json();
  const ctx = $("#grafico-faturamento");
  if (graficoFaturamento) graficoFaturamento.destroy();
  graficoFaturamento = new Chart(ctx, {
    type: "bar",
    data: {
      labels: dados.map((d) => d.data),
      datasets: [
        {
          label: "Faturamento (R$)",
          data: dados.map((d) => Number(d.total)),
          backgroundColor: "#E8A33D",
        },
      ],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

async function carregarGraficoProdutos() {
  const resp = await fetch(
    `${API}/relatorios/produtos-mais-vendidos?${periodoSelecionado()}`
  );
  const dados = await resp.json();
  const ctx = $("#grafico-produtos");
  if (graficoProdutos) graficoProdutos.destroy();
  graficoProdutos = new Chart(ctx, {
    type: "bar",
    data: {
      labels: dados.map((d) => d.produto_nome),
      datasets: [
        {
          label: "Quantidade vendida",
          data: dados.map((d) => d.quantidade_total),
          backgroundColor: "#7A1F1F",
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });
}

async function buscarPedidos() {
  const params = periodoSelecionado();
  const cliente = $("#busca-cliente").value.trim();
  if (cliente) params.set("cliente_nome", cliente);
  const resp = await fetch(`${API}/pedidos?${params}`);
  const pedidos = await resp.json();
  const tbody = $("#lista-pedidos-busca");
  tbody.innerHTML = "";
  $("#busca-vazia").hidden = pedidos.length > 0;
  for (const p of pedidos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${esc(p.cliente_nome)}</td>
      <td>${p.quantidade_itens}</td>
      <td>${brl(p.total)}</td>
      <td>${p.status}</td>
      <td>${new Date(p.criado_em).toLocaleString("pt-BR")}</td>`;
    tbody.appendChild(tr);
  }
}

async function recarregarTudo() {
  try {
    await Promise.all([
      carregarResumo(),
      carregarGraficoFaturamento(),
      carregarGraficoProdutos(),
      buscarPedidos(),
    ]);
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
}

$("#form-filtro").addEventListener("submit", (e) => {
  e.preventDefault();
  recarregarTudo();
});
$("#form-busca").addEventListener("submit", (e) => {
  e.preventDefault();
  buscarPedidos();
});
initMenu();

(async function iniciar() {
  const usuario = await verificarSessao("admin");
  if (!usuario) return;
  aplicarUsuarioNoMenu(usuario);
  await recarregarTudo();
})();
```

- [ ] **Passo 3: Estilos em `frontend/styles.css`**

Acrescento ao fim do arquivo:

```css
.cards-resumo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.card-resumo {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.card-resumo small { color: var(--muted); }
.card-resumo strong { font-size: 1.5rem; font-family: "Fraunces", serif; }

#secao-graficos canvas { max-width: 100%; margin-bottom: 24px; }

#form-filtro, #form-busca {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
  margin: 10px 0 16px;
}
#form-filtro label, #form-busca label { margin-bottom: 0; }
```

- [ ] **Passo 4: Smoke test da página**

Em `backend/tests/test_frontend.py`, acrescento:

```python
def test_relatorios_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/relatorios.html")
    assert resp.status_code == 200
    assert "Relatórios" in resp.text
    assert "relatorios.js" in resp.text
```

- [ ] **Passo 5: Rodar a suíte inteira**

```bash
cd backend && pytest -v
```
Esperado: **79 passed**.

- [ ] **Passo 6: Testar manualmente**

```bash
cd backend && rm -f app.db && uvicorn app.main:app --reload
```

Faço login como admin, crio 2-3 pedidos pela tela de Pedidos, abro
"Relatórios" pelo menu — confiro os cards de resumo, os dois gráficos e a
busca por nome de cliente. Testo também logar como atendente (preciso
criar um usuário atendente direto no banco pra isso, já que não há tela de
cadastro — ou simplesmente confio nos testes automatizados pra essa
cobertura) e confirmo que "Gerenciar Cardápio"/"Relatórios" somem do menu.

- [ ] **Passo 7: Atualizar o README**

Em `README.md`:
- No parágrafo de abertura, acrescento uma frase sobre a Fase 3.
- Na seção "Estrutura", acrescento `login.html`/`relatorios.html` na lista
  de páginas.
- Na tabela "Roadmap", troco o status da Fase 3 de `🔜 Próxima entrega`
  para `✅ Feito`.

- [ ] **Passo 8: Commit**

```bash
git add frontend/relatorios.html frontend/relatorios.js frontend/styles.css README.md backend/tests/test_frontend.py
git commit -m "feat: pagina de relatorios com graficos e busca de pedidos"
```

---

## Depois de terminar

Com as 6 tarefas prontas: `cd backend && pytest -v` deve mostrar **79
passed**. Abro o app, confiro o fluxo completo (login → pedidos →
cardápio → relatórios → logout) uma última vez, e sigo pro fluxo normal de
abrir PR / revisão.
