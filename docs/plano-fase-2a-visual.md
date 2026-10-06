# Fase 2a — Melhorias visuais — Plano de implementação

> Uso o skill `subagent-driven-development` (recomendado) ou `executing-plans`
> pra seguir esse plano tarefa por tarefa. Os passos usam `- [ ]` pra eu
> marcar conforme termino.

**Objetivo:** repaginar as duas páginas no visual "Chapa Quente" (paleta,
tipografia, menu hambúrguer), trocar o campo de categoria por um com
sugestões, e colocar foto nos produtos (upload + 8 ilustrações originais
pro cardápio inicial).

**Arquitetura:** não mexe na API que já existe — acrescenta um endpoint
novo (`POST /api/produtos/{id}/imagem`, multipart) e uma coluna
(`imagem_url`). O resto é CSS/HTML/JS nas duas páginas que já existem.

**Stack:** a mesma da Fase 2a — Python 3.12, FastAPI, SQLAlchemy 2.x,
SQLite, Pydantic v2, pytest + httpx, HTML/CSS/JS puro.

## Regras que sigo

- Python **3.12**; back-end em `backend/`, front em `frontend/`.
- Continuo na branch `fase-2a` — é polimento do que já construí nessa
  mesma branch, o PR #8 ainda está aberto.
- Upload de imagem: só `.jpg`/`.jpeg`/`.png`/`.webp`, até 5 MB.
- Fotos enviadas pelo usuário vão pra `backend/uploads/produtos/` (fora do
  git); as ilustrações do seed vão pra `frontend/images/seed/` (dentro do
  git, fazem parte do app).
- `ProdutoIn` (o schema de criar/editar produto) **não** ganha campo de
  imagem — a foto só muda pelo endpoint novo.
- Cada teste roda com: `cd backend && pytest`.
- Escopo travado: só o que está neste plano. Nada de fluxo de status,
  conta ou cozinha (isso é a Fase 2b).

---

## Estrutura de arquivos

```
backend/
  app/
    models.py             # Produto ganha imagem_url
    schemas.py             # ProdutoOut ganha imagem_url
    uploads.py              # NOVO: validação e armazenamento de arquivo
    crud.py                  # salvar_imagem_produto; excluir_produto apaga arquivo
    main.py                   # monta /uploads como estático
    routers/produtos.py        # POST /{id}/imagem
    seed.py                     # cada item ganha imagem_url
  requirements.txt               # + python-multipart
  tests/
    test_produtos.py              # testes de upload + fixture uploads_tmp
    test_frontend.py               # smoke test de /images/seed/*.svg e dos elementos novos
frontend/
  index.html                       # header com menu hambúrguer; cards com <img>
  cardapio-admin.html                # header com menu; categoria com datalist; campo de foto
  app.js                              # initMenu(); imagem no card
  admin.js                             # initMenu(); datalist; upload de imagem
  styles.css                            # paleta nova, tipografia, menu, imagens
  images/seed/
    x-salada.svg, x-bacon.svg, x-tudo.svg, x-vegetariano.svg,
    batata-frita.svg, onion-rings.svg, refrigerante.svg, suco.svg,
    placeholder.svg
.gitignore                           # + backend/uploads/
```

---

## Tarefa 1: Paleta "Chapa Quente", tipografia e menu hambúrguer

**Arquivos:**
- Modifico: `frontend/styles.css`
- Modifico: `frontend/index.html`
- Modifico: `frontend/cardapio-admin.html`
- Modifico: `frontend/app.js`
- Modifico: `frontend/admin.js`

**Interfaces:**
- Produz: as variáveis CSS `--bg`, `--surface`, `--ink`, `--muted`,
  `--line`, `--header`, `--header-ink`, `--accent`, `--accent-ink` em
  `styles.css`, usadas pelas Tarefas seguintes. A função `initMenu()`
  (duplicada em `app.js` e `admin.js`, igual já faço com `api()`/`brl()`),
  que depende dos ids `#btn-menu` e `#menu-nav` existirem no HTML.

Essa tarefa é só visual — não toca no back-end, não quebra nenhum teste
existente (os 42 testes continuam passando sem mudança nenhuma nos
arquivos Python).

- [ ] **Passo 1: Substituir `frontend/styles.css` inteiro**

```css
* { box-sizing: border-box; }

:root {
  --bg: #FAF6EF;
  --surface: #FFFFFF;
  --ink: #2B2420;
  --muted: #8C7F6E;
  --line: #EADFCB;
  --header: #7A1F1F;
  --header-ink: #FBEADB;
  --accent: #E8A33D;
  --accent-ink: #3A2200;
}

body {
  margin: 0;
  font-family: "Work Sans", system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  color: var(--ink);
  background: var(--bg);
}

h1, h2, h3 {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 600;
}

header {
  background: var(--header);
  color: var(--header-ink);
  padding: 16px 24px;
  position: relative;
}
header h1 { margin: 0; font-size: 1.4rem; }

.hamb-btn {
  position: absolute;
  top: 14px;
  right: 20px;
  background: var(--accent);
  color: var(--accent-ink);
  border: 0;
  width: 38px;
  height: 38px;
  border-radius: 9px;
  font-size: 1.1rem;
  cursor: pointer;
}

.hamb-menu {
  position: absolute;
  top: 60px;
  right: 20px;
  background: var(--surface);
  border-radius: 10px;
  border: 1px solid var(--line);
  box-shadow: 0 10px 28px -10px rgba(50, 20, 0, 0.35);
  padding: 8px;
  display: flex;
  flex-direction: column;
  min-width: 170px;
  z-index: 20;
}
.hamb-menu a {
  padding: 9px 12px;
  border-radius: 7px;
  font-size: 0.9rem;
  color: var(--ink);
  text-decoration: none;
  font-weight: 500;
}
.hamb-menu a.active { background: #FBEFD9; color: #8A4200; }
.hamb-menu a:hover { background: #F6F1E6; }

main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
  display: grid;
  gap: 32px;
}
h2 { border-bottom: 2px solid var(--line); padding-bottom: 4px; font-size: 1.2rem; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 11px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 1px 0 var(--line);
}
.card small { color: var(--muted); }
.card .preco { font-weight: 700; color: var(--header); }
.card button { margin-top: auto; }

button {
  background: var(--header);
  color: var(--header-ink);
  border: 0;
  border-radius: 8px;
  padding: 9px 14px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
}
button.secundario { background: #6c757d; }
button.perigo { background: #8a1c10; }

form label { display: block; margin-bottom: 10px; font-size: 0.92rem; }
form input {
  display: block;
  width: 100%;
  padding: 9px 10px;
  margin-top: 4px;
  border: 1px solid var(--line);
  border-radius: 8px;
  font-family: inherit;
}
input[type="checkbox"] {
  display: inline-block;
  width: auto;
  margin-right: 6px;
}

#carrinho { list-style: none; padding: 0; display: grid; gap: 6px; }
#carrinho li {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 6px 10px;
}
#carrinho li span { flex: 1; }
#carrinho li input { width: 64px; }

table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 10px; overflow: hidden; }
th, td { border: 1px solid var(--line); padding: 9px 10px; text-align: left; font-size: 0.9rem; }
th { background: #F6F0E2; font-family: "Fraunces", serif; font-weight: 600; }

.acoes { display: flex; gap: 8px; }

.aviso {
  max-width: 960px;
  margin: 12px auto 0;
  padding: 10px 16px;
  border-radius: 8px;
}
.aviso.erro { background: #f8d7da; color: #842029; }
.aviso.ok { background: #d1e7dd; color: #0f5132; }
.detalhe-itens { background: #FBF3E3; }

@media (max-width: 600px) {
  table, thead, tbody, th, td, tr { display: block; }
  thead { display: none; }
  td { border: 0; border-bottom: 1px solid var(--line); }
}
```

Esse conteúdo substitui o arquivo `frontend/styles.css` inteiro (o arquivo
atual, incluindo as regras de `header nav`/checkbox que eu tinha
acrescentado na Fase 2a, deixa de existir — as regras de checkbox
continuam aqui, só as de `header nav a` saem porque os links viram menu).

- [ ] **Passo 2: Cabeçalho de `frontend/index.html`**

No `<head>`, troco:
```html
  <link rel="stylesheet" href="styles.css" />
```
por:
```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Work+Sans:wght@400;500;600&display=swap">
  <link rel="stylesheet" href="styles.css" />
```

No `<body>`, troco:
```html
  <header>
    <h1>🍔 Hamburgueria — Pedidos</h1>
    <nav><a href="/cardapio-admin.html">Gerenciar cardápio</a></nav>
  </header>
```
por:
```html
  <header>
    <h1>🍔 Hamburgueria — Pedidos</h1>
    <button class="hamb-btn" id="btn-menu" aria-label="Abrir menu" aria-expanded="false">☰</button>
    <nav class="hamb-menu" id="menu-nav" hidden>
      <a href="/" class="active">Pedidos</a>
      <a href="/cardapio-admin.html">Cardápio</a>
    </nav>
  </header>
```

- [ ] **Passo 3: Cabeçalho de `frontend/cardapio-admin.html`**

No `<head>`, mesma troca do Passo 2 (acrescentar os dois `<link>` de fonte
antes do `<link rel="stylesheet" href="styles.css" />`).

No `<body>`, troco:
```html
  <header>
    <h1>🍔 Hamburgueria — Cardápio</h1>
    <nav><a href="/">Pedidos</a></nav>
  </header>
```
por:
```html
  <header>
    <h1>🍔 Hamburgueria — Cardápio</h1>
    <button class="hamb-btn" id="btn-menu" aria-label="Abrir menu" aria-expanded="false">☰</button>
    <nav class="hamb-menu" id="menu-nav" hidden>
      <a href="/">Pedidos</a>
      <a href="/cardapio-admin.html" class="active">Cardápio</a>
    </nav>
  </header>
```

- [ ] **Passo 4: `initMenu()` em `frontend/app.js`**

Troco:
```js
function brl(valorStr) {
  const n = Number(valorStr || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function api(caminho, opcoes) {
```
por:
```js
function brl(valorStr) {
  const n = Number(valorStr || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
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

async function api(caminho, opcoes) {
```

E troco:
```js
$("#form-pedido").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);

(async function iniciar() {
```
por:
```js
$("#form-pedido").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);
initMenu();

(async function iniciar() {
```

- [ ] **Passo 5: `initMenu()` em `frontend/admin.js`**

Mesmas duas trocas do Passo 4, só que no arquivo `frontend/admin.js` — a
função `initMenu` é idêntica (copio o mesmo código), e o segundo trecho é:

Troco:
```js
$("#form-produto").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);

(async function iniciar() {
```
por:
```js
$("#form-produto").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);
initMenu();

(async function iniciar() {
```

- [ ] **Passo 6: Rodar a suíte (nada de Python mudou, só confirmando)**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo (42 testes, nenhum deles olha CSS/JS).

- [ ] **Passo 7: Teste manual pelo navegador**

```bash
cd backend && uvicorn app.main:app --reload
```

Abro `http://localhost:8000` e confiro: a cor vinho no header, a fonte
serifada no título, o botão `☰` abrindo o menu dropdown com "Pedidos" /
"Cardápio", fechando ao clicar fora. Repito em
`http://localhost:8000/cardapio-admin.html`. Paro o servidor e apago o
`backend/app.db` gerado.

- [ ] **Passo 8: Commit**

```bash
git add frontend/
git commit -m "feat: paleta Chapa Quente, tipografia e menu hamburguer"
```

---

## Tarefa 2: Categoria com sugestões (datalist)

**Arquivos:**
- Modifico: `frontend/cardapio-admin.html`
- Modifico: `frontend/admin.js`

**Interfaces:**
- Produz: `atualizarListaCategorias(produtos)` em `admin.js`, chamada
  dentro de `carregarProdutos()` — a Tarefa 5 builda em cima dessa mesma
  função sem mudar sua assinatura.

- [ ] **Passo 1: Campo de categoria em `frontend/cardapio-admin.html`**

Troco:
```html
        <label>Categoria
          <input type="text" id="categoria" maxlength="40" required />
        </label>
```
por:
```html
        <label>Categoria
          <input type="text" id="categoria" maxlength="40" required list="categorias-lista" />
          <datalist id="categorias-lista"></datalist>
        </label>
```

- [ ] **Passo 2: `atualizarListaCategorias` em `frontend/admin.js`**

Troco:
```js
async function carregarProdutos() {
  const produtos = await api("/produtos?incluir_indisponiveis=true");
  const tbody = $("#lista-produtos");
```
por:
```js
function atualizarListaCategorias(produtos) {
  const categorias = [...new Set(produtos.map((p) => p.categoria))].sort();
  $("#categorias-lista").innerHTML = categorias
    .map((c) => `<option value="${c}"></option>`)
    .join("");
}

async function carregarProdutos() {
  const produtos = await api("/produtos?incluir_indisponiveis=true");
  atualizarListaCategorias(produtos);
  const tbody = $("#lista-produtos");
```

- [ ] **Passo 3: Rodar a suíte**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo.

- [ ] **Passo 4: Teste manual**

```bash
cd backend && uvicorn app.main:app --reload
```

Abro `http://localhost:8000/cardapio-admin.html`, clico no campo
"Categoria" e confiro que aparecem as 4 categorias do seed
(Clássicos/Especiais/Acompanhamentos/Bebidas) como sugestão, e que ainda
dá pra digitar uma categoria nova. Paro o servidor e apago o `app.db`.

- [ ] **Passo 5: Commit**

```bash
git add frontend/cardapio-admin.html frontend/admin.js
git commit -m "feat: campo de categoria com sugestoes (datalist)"
```

---

## Tarefa 3: Back-end do upload de imagem

**Arquivos:**
- Cria: `backend/app/uploads.py`
- Modifico: `backend/app/models.py`
- Modifico: `backend/app/schemas.py`
- Modifico: `backend/app/crud.py`
- Modifico: `backend/app/routers/produtos.py`
- Modifico: `backend/app/main.py`
- Modifico: `backend/requirements.txt`
- Modifico: `.gitignore`
- Teste: `backend/tests/test_produtos.py`

**Interfaces:**
- Produz: `models.Produto.imagem_url: str | None`.
  `uploads.PRODUTOS_DIR`, `uploads.extensao_valida(nome) -> str | None`,
  `uploads.salvar_arquivo(produto_id, extensao, conteudo) -> str`,
  `uploads.remover_arquivo(imagem_url)`, `uploads.UPLOADS_ROOT`.
  `crud.salvar_imagem_produto(db, produto_id, arquivo) -> models.Produto | None`
  (levanta `RegraNegocioError` em formato/tamanho inválido). Rota nova
  `POST /api/produtos/{id}/imagem`.

- [ ] **Passo 1: `backend/app/uploads.py`**

```python
import os
from pathlib import Path
from uuid import uuid4

_DEFAULT_UPLOADS_ROOT = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_ROOT = Path(os.environ.get("UPLOADS_DIR", str(_DEFAULT_UPLOADS_ROOT)))
PRODUTOS_DIR = UPLOADS_ROOT / "produtos"
PRODUTOS_DIR.mkdir(parents=True, exist_ok=True)

EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB


def extensao_valida(nome_arquivo: str) -> str | None:
    ext = Path(nome_arquivo).suffix.lower()
    return ext if ext in EXTENSOES_PERMITIDAS else None


def salvar_arquivo(produto_id: int, extensao: str, conteudo: bytes) -> str:
    nome = f"{produto_id}-{uuid4().hex[:8]}{extensao}"
    (PRODUTOS_DIR / nome).write_bytes(conteudo)
    return f"/uploads/produtos/{nome}"


def remover_arquivo(imagem_url: str | None) -> None:
    if not imagem_url or not imagem_url.startswith("/uploads/produtos/"):
        return
    (PRODUTOS_DIR / Path(imagem_url).name).unlink(missing_ok=True)
```

- [ ] **Passo 2: `imagem_url` em `backend/app/models.py`**

Na classe `Produto`, troco:
```python
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)
```
por:
```python
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)
    imagem_url: Mapped[str | None] = mapped_column(String(255), default=None)
```

- [ ] **Passo 3: `imagem_url` em `backend/app/schemas.py`**

Na classe `ProdutoOut`, troco:
```python
    categoria: str
    disponivel: bool
```
por:
```python
    categoria: str
    disponivel: bool
    imagem_url: str | None = None
```

`ProdutoIn` **não muda** — a foto não entra no corpo JSON de criar/editar
produto, só pelo endpoint novo.

- [ ] **Passo 4: Teste que falha, pra provar que o endpoint ainda não existe**

Acrescento ao fim de `backend/tests/test_produtos.py`, depois de importar
o módulo novo logo no topo do arquivo (troco a linha `from app import
models` por `from app import models, uploads`):

```python
import base64

_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def uploads_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "PRODUTOS_DIR", tmp_path)
    return tmp_path


def test_upload_imagem_produto(client: TestClient, uploads_tmp) -> None:
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["imagem_url"].startswith("/uploads/produtos/1-")
    assert len(list(uploads_tmp.iterdir())) == 1


def test_upload_imagem_substitui_anterior(client: TestClient, uploads_tmp) -> None:
    client.post("/api/produtos/1/imagem", files={"arquivo": ("a.png", _PNG_1X1, "image/png")})
    client.post("/api/produtos/1/imagem", files={"arquivo": ("b.png", _PNG_1X1, "image/png")})
    assert len(list(uploads_tmp.iterdir())) == 1


def test_upload_imagem_formato_invalido_400(client: TestClient, uploads_tmp) -> None:
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("doc.txt", b"nao e imagem", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_imagem_produto_inexistente_404(client: TestClient, uploads_tmp) -> None:
    resp = client.post(
        "/api/produtos/999/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 404


def test_upload_imagem_muito_grande_400(client: TestClient, uploads_tmp) -> None:
    conteudo_grande = b"0" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/produtos/1/imagem",
        files={"arquivo": ("foto.png", conteudo_grande, "image/png")},
    )
    assert resp.status_code == 400


def test_excluir_produto_remove_arquivo_de_imagem(client: TestClient, uploads_tmp) -> None:
    criado = client.post("/api/produtos", json=PRODUTO_NOVO).json()
    client.post(
        f"/api/produtos/{criado['id']}/imagem",
        files={"arquivo": ("foto.png", _PNG_1X1, "image/png")},
    )
    assert len(list(uploads_tmp.iterdir())) == 1

    client.delete(f"/api/produtos/{criado['id']}")
    assert len(list(uploads_tmp.iterdir())) == 0
```

Preciso também acrescentar `import pytest` no topo do arquivo, se ainda
não tiver (confiro antes de duplicar o import).

Também atualizo `test_get_produtos_retorna_seed`, que vai começar a falhar
porque a resposta ganhou um campo novo — troco:
```python
    assert set(primeiro) == {
        "id", "nome", "descricao", "preco", "categoria", "disponivel"
    }
```
por:
```python
    assert set(primeiro) == {
        "id", "nome", "descricao", "preco", "categoria", "disponivel", "imagem_url"
    }
```

- [ ] **Passo 5: Rodar e ver falhar**

Rodo: `cd backend && pytest tests/test_produtos.py -v`
Espero: FAIL — `404`/`405` nos testes de upload (rota não existe ainda) e
`AssertionError` no `test_get_produtos_retorna_seed` (falta a chave
`imagem_url`, que já existe no schema desde o Passo 3 mas eu rodo o teste
só depois de confirmar a falha, antes de implementar o resto).

- [ ] **Passo 6: `salvar_imagem_produto` em `backend/app/crud.py`**

No topo do arquivo, troco:
```python
from app import models, schemas
```
por:
```python
from app import models, schemas, uploads
```

Acrescento, depois de `atualizar_produto`:

```python
async def salvar_imagem_produto(
    db: Session, produto_id: int, arquivo
) -> models.Produto | None:
    produto = db.get(models.Produto, produto_id)
    if produto is None:
        return None
    extensao = uploads.extensao_valida(arquivo.filename or "")
    if extensao is None:
        raise RegraNegocioError(
            "Formato de imagem não suportado. Use JPG, PNG ou WEBP."
        )
    conteudo = await arquivo.read()
    if len(conteudo) > uploads.TAMANHO_MAXIMO_BYTES:
        raise RegraNegocioError("Imagem muito grande — o limite é 5 MB.")
    uploads.remover_arquivo(produto.imagem_url)
    produto.imagem_url = uploads.salvar_arquivo(produto_id, extensao, conteudo)
    db.commit()
    db.refresh(produto)
    return produto
```

(Deixo o parâmetro `arquivo` sem anotação de tipo de propósito — ele é um
`UploadFile` do FastAPI, mas `crud.py` nunca importou nada do FastAPI até
agora, e quero manter essa camada sem depender do framework web.)

Em `excluir_produto`, troco:
```python
    if em_uso:
        raise RegraNegocioError(
            "Não é possível excluir — esse produto já aparece em pedidos. "
            "Marque como indisponível em vez de excluir."
        )
    db.delete(produto)
```
por:
```python
    if em_uso:
        raise RegraNegocioError(
            "Não é possível excluir — esse produto já aparece em pedidos. "
            "Marque como indisponível em vez de excluir."
        )
    uploads.remover_arquivo(produto.imagem_url)
    db.delete(produto)
```

- [ ] **Passo 7: Rota em `backend/app/routers/produtos.py`**

No topo, troco:
```python
from fastapi import APIRouter, Depends, HTTPException, status
```
por:
```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
```

Acrescento no fim do arquivo:

```python
@router.post("/{produto_id}/imagem", response_model=schemas.ProdutoOut)
async def enviar_imagem(
    produto_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        produto = await crud.salvar_imagem_produto(db, produto_id, arquivo)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem) from erro
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto
```

- [ ] **Passo 8: Montar `/uploads` em `backend/app/main.py`**

Troco:
```python
from app import models  # noqa: F401  -- registra as tabelas em Base.metadata
from app.database import Base, SessionLocal, engine
```
por:
```python
from app import models  # noqa: F401  -- registra as tabelas em Base.metadata
from app.database import Base, SessionLocal, engine
from app.uploads import UPLOADS_ROOT
```

E troco:
```python
    if FRONTEND_DIR.is_dir():
        app.mount(
            "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
        )

    return app
```
por (o mount de `/uploads` precisa vir **antes** do de `/`, senão o mount
de `/` — que é um catch-all — intercepta a rota primeiro):
```python
    if UPLOADS_ROOT.is_dir():
        app.mount("/uploads", StaticFiles(directory=UPLOADS_ROOT), name="uploads")

    if FRONTEND_DIR.is_dir():
        app.mount(
            "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
        )

    return app
```

- [ ] **Passo 9: Dependência nova**

Acrescento no fim de `backend/requirements.txt`:
```
python-multipart==0.0.9
```
(O FastAPI precisa desse pacote pra ler `multipart/form-data` — sem ele, a
rota de upload dá erro 500 na primeira chamada.)

- [ ] **Passo 10: `.gitignore`**

Acrescento uma linha:
```
backend/uploads/
```

- [ ] **Passo 11: Rodar e ver passar**

Rodo: `cd backend && pip install -r requirements.txt && pytest -v`
Espero: PASS em tudo (os 42 de antes + os 6 novos de upload = 48). Saída
sem warning.

- [ ] **Passo 12: Commit**

```bash
git add backend/ .gitignore
git commit -m "feat: upload de imagem de produto (POST /api/produtos/{id}/imagem)"
```

---

## Tarefa 4: Ilustrações do cardápio inicial

**Arquivos:**
- Cria: `frontend/images/seed/x-salada.svg`
- Cria: `frontend/images/seed/x-bacon.svg`
- Cria: `frontend/images/seed/x-tudo.svg`
- Cria: `frontend/images/seed/x-vegetariano.svg`
- Cria: `frontend/images/seed/batata-frita.svg`
- Cria: `frontend/images/seed/onion-rings.svg`
- Cria: `frontend/images/seed/refrigerante.svg`
- Cria: `frontend/images/seed/suco.svg`
- Cria: `frontend/images/seed/placeholder.svg`
- Modifico: `backend/app/seed.py`
- Teste: `backend/tests/test_produtos.py`, `backend/tests/test_frontend.py`

**Interfaces:**
- Produz: os 9 arquivos SVG servidos em `/images/seed/<arquivo>.svg`
  (dentro do mount que já existe pro `frontend/`). `CARDAPIO_INICIAL`
  ganha a chave `imagem_url` em cada item — usada pela Tarefa 5 no front.

Copio o SVG de cada arquivo **exatamente como está abaixo** — são
ilustrações simples (desenhei com formas geométricas: círculos, retângulos
arredondados, caminhos), no esquema de cor do cardápio (pão dourado,
carne marrom, queijo amarelo, alface verde, tomate vermelho).

- [ ] **Passo 1: `frontend/images/seed/x-salada.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <ellipse cx="80" cy="118" rx="46" ry="12" fill="#D98B2E"/>
  <path d="M38 108 Q40 92 60 92 L100 92 Q120 92 122 108 Z" fill="#7A9A3D"/>
  <rect x="42" y="96" width="76" height="14" rx="6" fill="#6B4226"/>
  <path d="M40 92 Q42 78 60 80 L100 80 Q118 78 120 92 Z" fill="#C23B2B"/>
  <path d="M34 78 Q34 50 80 46 Q126 50 126 78 Q126 86 118 86 L42 86 Q34 86 34 78 Z" fill="#E8A33D"/>
  <circle cx="60" cy="58" r="2.4" fill="#FBEFD9"/>
  <circle cx="75" cy="52" r="2.4" fill="#FBEFD9"/>
  <circle cx="92" cy="54" r="2.4" fill="#FBEFD9"/>
  <circle cx="106" cy="60" r="2.4" fill="#FBEFD9"/>
  <circle cx="68" cy="66" r="2.4" fill="#FBEFD9"/>
  <circle cx="98" cy="68" r="2.4" fill="#FBEFD9"/>
</svg>
```

- [ ] **Passo 2: `frontend/images/seed/x-bacon.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <ellipse cx="80" cy="118" rx="46" ry="12" fill="#D98B2E"/>
  <rect x="42" y="98" width="76" height="14" rx="6" fill="#6B4226"/>
  <path d="M40 94 Q80 102 120 94 L120 100 Q80 108 40 100 Z" fill="#F2C14E"/>
  <path d="M38 86 Q58 78 76 88 Q94 80 122 86 L120 94 Q92 84 76 92 Q60 84 40 94 Z" fill="#8B3A2B"/>
  <path d="M42 80 Q62 73 78 82 Q96 74 118 80 L116 86 Q96 80 78 87 Q62 79 44 86 Z" fill="#D98B2E"/>
  <path d="M34 76 Q34 48 80 44 Q126 48 126 76 Q126 84 118 84 L42 84 Q34 84 34 76 Z" fill="#E8A33D"/>
  <circle cx="60" cy="56" r="2.4" fill="#FBEFD9"/>
  <circle cx="75" cy="50" r="2.4" fill="#FBEFD9"/>
  <circle cx="92" cy="52" r="2.4" fill="#FBEFD9"/>
  <circle cx="106" cy="58" r="2.4" fill="#FBEFD9"/>
</svg>
```

- [ ] **Passo 3: `frontend/images/seed/x-tudo.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <ellipse cx="80" cy="128" rx="46" ry="11" fill="#D98B2E"/>
  <rect x="42" y="110" width="76" height="13" rx="6" fill="#6B4226"/>
  <path d="M38 102 Q40 90 58 90 L102 90 Q120 90 122 102 Z" fill="#7A9A3D"/>
  <ellipse cx="80" cy="92" rx="26" ry="8" fill="#FFFFFF"/>
  <circle cx="80" cy="92" r="6" fill="#F2C14E"/>
  <rect x="44" y="78" width="72" height="13" rx="6" fill="#6B4226"/>
  <path d="M40 74 Q60 67 76 76 Q94 68 120 74 L118 80 Q96 74 76 81 Q60 73 42 80 Z" fill="#8B3A2B"/>
  <path d="M34 66 Q34 42 80 38 Q126 42 126 66 Q126 74 118 74 L42 74 Q34 74 34 66 Z" fill="#E8A33D"/>
  <circle cx="60" cy="48" r="2.2" fill="#FBEFD9"/>
  <circle cx="75" cy="43" r="2.2" fill="#FBEFD9"/>
  <circle cx="92" cy="45" r="2.2" fill="#FBEFD9"/>
  <circle cx="106" cy="50" r="2.2" fill="#FBEFD9"/>
</svg>
```

- [ ] **Passo 4: `frontend/images/seed/x-vegetariano.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#F2F0E2"/>
  <ellipse cx="80" cy="118" rx="46" ry="12" fill="#D98B2E"/>
  <path d="M38 108 Q40 92 60 92 L100 92 Q120 92 122 108 Z" fill="#5B6B2F"/>
  <rect x="42" y="96" width="76" height="14" rx="6" fill="#8FA357"/>
  <ellipse cx="58" cy="90" rx="6" ry="3.5" fill="#6B2A1F"/>
  <ellipse cx="100" cy="91" rx="6" ry="3.5" fill="#6B2A1F"/>
  <path d="M40 92 Q42 78 60 80 L100 80 Q118 78 120 92 Z" fill="#7A9A3D"/>
  <path d="M34 78 Q34 50 80 46 Q126 50 126 78 Q126 86 118 86 L42 86 Q34 86 34 78 Z" fill="#E8A33D"/>
  <circle cx="60" cy="58" r="2.4" fill="#FBEFD9"/>
  <circle cx="75" cy="52" r="2.4" fill="#FBEFD9"/>
  <circle cx="92" cy="54" r="2.4" fill="#FBEFD9"/>
  <circle cx="106" cy="60" r="2.4" fill="#FBEFD9"/>
</svg>
```

- [ ] **Passo 5: `frontend/images/seed/batata-frita.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <rect x="68" y="42" width="7" height="58" rx="3" fill="#F2C14E" transform="rotate(-8 71 71)"/>
  <rect x="80" y="38" width="7" height="62" rx="3" fill="#F2C14E"/>
  <rect x="92" y="42" width="7" height="58" rx="3" fill="#F2C14E" transform="rotate(8 95 71)"/>
  <rect x="58" y="48" width="7" height="50" rx="3" fill="#D98B2E" transform="rotate(-16 61 73)"/>
  <rect x="102" y="48" width="7" height="50" rx="3" fill="#D98B2E" transform="rotate(16 105 73)"/>
  <path d="M52 92 L108 92 L100 130 Q100 134 96 134 L64 134 Q60 134 60 130 Z" fill="#FFFFFF" stroke="#C23B2B" stroke-width="5"/>
  <path d="M52 92 L108 92 L105 104 L55 104 Z" fill="#C23B2B"/>
</svg>
```

- [ ] **Passo 6: `frontend/images/seed/onion-rings.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <ellipse cx="80" cy="120" rx="40" ry="8" fill="#EADFCB"/>
  <ellipse cx="80" cy="100" rx="38" ry="15" fill="none" stroke="#E8A33D" stroke-width="12"/>
  <ellipse cx="80" cy="100" rx="38" ry="15" fill="none" stroke="#D98B2E" stroke-width="3"/>
  <ellipse cx="80" cy="78" rx="34" ry="13" fill="none" stroke="#F2C14E" stroke-width="11"/>
  <ellipse cx="80" cy="78" rx="34" ry="13" fill="none" stroke="#D98B2E" stroke-width="3"/>
  <ellipse cx="80" cy="56" rx="30" ry="12" fill="none" stroke="#E8A33D" stroke-width="10"/>
  <ellipse cx="80" cy="56" rx="30" ry="12" fill="none" stroke="#D98B2E" stroke-width="3"/>
</svg>
```

- [ ] **Passo 7: `frontend/images/seed/refrigerante.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <rect x="56" y="36" width="48" height="92" rx="10" fill="#C23B2B"/>
  <rect x="56" y="70" width="48" height="26" fill="#FBEADB"/>
  <ellipse cx="80" cy="36" rx="24" ry="6" fill="#D98B2E"/>
  <rect x="74" y="28" width="12" height="10" rx="2" fill="#D98B2E"/>
  <circle cx="44" cy="58" r="3.5" fill="#CFE6F2"/>
  <circle cx="40" cy="72" r="2.5" fill="#CFE6F2"/>
  <circle cx="118" cy="66" r="3" fill="#CFE6F2"/>
</svg>
```

- [ ] **Passo 8: `frontend/images/seed/suco.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#FBF3E3"/>
  <path d="M54 42 L106 42 L96 126 Q95 130 91 130 L69 130 Q65 130 64 126 Z" fill="#F2C14E"/>
  <path d="M54 42 L106 42 L103 58 L57 58 Z" fill="#FBEADB" opacity="0.55"/>
  <rect x="86" y="24" width="7" height="46" rx="3" fill="#E8A33D" transform="rotate(18 90 47)"/>
  <circle cx="68" cy="40" r="12" fill="#D98B2E"/>
  <path d="M68 30 L68 50 M58 40 L78 40" stroke="#FBEADB" stroke-width="2.5"/>
</svg>
```

- [ ] **Passo 9: `frontend/images/seed/placeholder.svg`**

```svg
<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
  <circle cx="80" cy="80" r="76" fill="#F2EEE3"/>
  <circle cx="80" cy="80" r="40" fill="none" stroke="#C9BBA3" stroke-width="4"/>
  <path d="M62 66 L98 94 M98 66 L62 94" stroke="#C9BBA3" stroke-width="5" stroke-linecap="round"/>
</svg>
```

- [ ] **Passo 10: `imagem_url` em `backend/app/seed.py`**

Troco `CARDAPIO_INICIAL` inteiro — cada item ganha a chave `imagem_url`:

```python
CARDAPIO_INICIAL: list[dict] = [
    {"nome": "X-Salada", "descricao": "Hambúrguer, queijo, alface, tomate e maionese",
     "preco": Decimal("18.00"), "categoria": "Clássicos",
     "imagem_url": "/images/seed/x-salada.svg"},
    {"nome": "X-Bacon", "descricao": "Hambúrguer, queijo, bacon crocante e maionese",
     "preco": Decimal("22.00"), "categoria": "Clássicos",
     "imagem_url": "/images/seed/x-bacon.svg"},
    {"nome": "X-Tudo", "descricao": "Dois hambúrgueres, queijo, bacon, ovo, salada e batata palha",
     "preco": Decimal("28.00"), "categoria": "Especiais",
     "imagem_url": "/images/seed/x-tudo.svg"},
    {"nome": "X-Vegetariano", "descricao": "Hambúrguer de grão-de-bico, queijo, rúcula e tomate seco",
     "preco": Decimal("24.00"), "categoria": "Especiais",
     "imagem_url": "/images/seed/x-vegetariano.svg"},
    {"nome": "Batata Frita", "descricao": "Porção individual de batata frita",
     "preco": Decimal("12.00"), "categoria": "Acompanhamentos",
     "imagem_url": "/images/seed/batata-frita.svg"},
    {"nome": "Onion Rings", "descricao": "Anéis de cebola empanados",
     "preco": Decimal("14.00"), "categoria": "Acompanhamentos",
     "imagem_url": "/images/seed/onion-rings.svg"},
    {"nome": "Refrigerante Lata", "descricao": "350 ml",
     "preco": Decimal("6.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/refrigerante.svg"},
    {"nome": "Suco Natural", "descricao": "Copo 300 ml, sabores do dia",
     "preco": Decimal("9.00"), "categoria": "Bebidas",
     "imagem_url": "/images/seed/suco.svg"},
]
```

- [ ] **Passo 11: Teste confirmando que o seed grava a imagem**

Acrescento ao fim de `backend/tests/test_produtos.py`:

```python
def test_seed_grava_imagem_de_cada_item(db_session: Session) -> None:
    seed_cardapio(db_session)
    produtos = db_session.query(models.Produto).all()
    assert all(p.imagem_url is not None for p in produtos)
    assert all(p.imagem_url.startswith("/images/seed/") for p in produtos)
```

E, em `backend/tests/test_frontend.py`, acrescento:

```python
def test_ilustracao_do_seed_e_servida(client: TestClient) -> None:
    resp = client.get("/images/seed/x-salada.svg")
    assert resp.status_code == 200
    assert "<svg" in resp.text


def test_placeholder_de_imagem_e_servido(client: TestClient) -> None:
    resp = client.get("/images/seed/placeholder.svg")
    assert resp.status_code == 200
    assert "<svg" in resp.text
```

- [ ] **Passo 12: Rodar e ver passar**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo (48 de antes + 3 novos = 51).

- [ ] **Passo 13: Commit**

```bash
git add frontend/images/ backend/app/seed.py backend/tests/
git commit -m "feat: ilustracoes SVG do cardapio inicial"
```

---

## Tarefa 5: Front-end — mostrar e enviar foto do produto

**Arquivos:**
- Modifico: `frontend/app.js`
- Modifico: `frontend/admin.js`
- Modifico: `frontend/cardapio-admin.html`
- Modifico: `frontend/styles.css`
- Teste: `backend/tests/test_frontend.py`

**Interfaces:**
- Consome: `GET /api/produtos` (já traz `imagem_url`, desde a Tarefa 3),
  `POST /api/produtos/{id}/imagem` (Tarefa 3), `atualizarListaCategorias`
  (Tarefa 2, não mexo nela — só acrescento código ao redor).

- [ ] **Passo 1: Estilo das imagens em `frontend/styles.css`**

Acrescento no fim do arquivo:

```css
.card-img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 8px;
  background: #F6F0E2;
}
.thumb {
  width: 44px;
  height: 44px;
  object-fit: cover;
  border-radius: 6px;
  background: #F6F0E2;
  display: block;
}
.preview-img {
  max-width: 160px;
  max-height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--line);
  margin-top: 6px;
}
```

- [ ] **Passo 2: Foto nos cards do cardápio — `frontend/app.js`**

Troco:
```js
    div.innerHTML = `
      <strong>${p.nome}</strong>
      <small>${p.categoria}</small>
      <span>${p.descricao ?? ""}</span>
      <span class="preco">${brl(p.preco)}</span>
      <button type="button" data-id="${p.id}">Adicionar</button>`;
```
por:
```js
    div.innerHTML = `
      <img class="card-img" src="${p.imagem_url || "/images/seed/placeholder.svg"}" alt="${p.nome}" />
      <strong>${p.nome}</strong>
      <small>${p.categoria}</small>
      <span>${p.descricao ?? ""}</span>
      <span class="preco">${brl(p.preco)}</span>
      <button type="button" data-id="${p.id}">Adicionar</button>`;
```

- [ ] **Passo 3: Campo de foto em `frontend/cardapio-admin.html`**

Troco:
```html
        <label>
          <input type="checkbox" id="disponivel" checked />
          Disponível
        </label>

        <div class="acoes">
```
por:
```html
        <label>
          <input type="checkbox" id="disponivel" checked />
          Disponível
        </label>
        <label>Foto do produto
          <input type="file" id="imagem" accept="image/jpeg,image/png,image/webp" />
        </label>
        <img id="preview-imagem" class="preview-img" hidden alt="Prévia da foto" />

        <div class="acoes">
```

E troco o cabeçalho da tabela:
```html
          <tr>
            <th>Nome</th><th>Categoria</th><th>Preço</th>
            <th>Disponível</th><th></th>
          </tr>
```
por:
```html
          <tr>
            <th>Foto</th><th>Nome</th><th>Categoria</th><th>Preço</th>
            <th>Disponível</th><th></th>
          </tr>
```

- [ ] **Passo 4: Upload e prévia em `frontend/admin.js`**

Troco:
```js
let editandoId = null;
```
por:
```js
let editandoId = null;
let arquivoSelecionado = null;
```

Troco `entrarModoEdicao` inteira:
```js
function entrarModoEdicao(produto) {
  editandoId = produto.id;
  $("#form-titulo").textContent = `Editar produto #${produto.id}`;
  $("#btn-salvar").textContent = "Salvar alterações";
  $("#btn-cancelar").hidden = false;
  $("#nome").value = produto.nome;
  $("#descricao").value = produto.descricao ?? "";
  $("#preco").value = produto.preco;
  $("#categoria").value = produto.categoria;
  $("#disponivel").checked = produto.disponivel;
  $("#secao-form").scrollIntoView({ behavior: "smooth" });
}
```
por:
```js
function entrarModoEdicao(produto) {
  editandoId = produto.id;
  arquivoSelecionado = null;
  $("#imagem").value = "";
  $("#form-titulo").textContent = `Editar produto #${produto.id}`;
  $("#btn-salvar").textContent = "Salvar alterações";
  $("#btn-cancelar").hidden = false;
  $("#nome").value = produto.nome;
  $("#descricao").value = produto.descricao ?? "";
  $("#preco").value = produto.preco;
  $("#categoria").value = produto.categoria;
  $("#disponivel").checked = produto.disponivel;
  const preview = $("#preview-imagem");
  if (produto.imagem_url) {
    preview.src = produto.imagem_url;
    preview.hidden = false;
  } else {
    preview.hidden = true;
  }
  $("#secao-form").scrollIntoView({ behavior: "smooth" });
}
```

Troco `sairModoEdicao` inteira:
```js
function sairModoEdicao() {
  editandoId = null;
  $("#form-titulo").textContent = "Novo produto";
  $("#btn-salvar").textContent = "Salvar produto";
  $("#btn-cancelar").hidden = true;
  $("#form-produto").reset();
  $("#disponivel").checked = true;
}
```
por:
```js
function sairModoEdicao() {
  editandoId = null;
  arquivoSelecionado = null;
  $("#form-titulo").textContent = "Novo produto";
  $("#btn-salvar").textContent = "Salvar produto";
  $("#btn-cancelar").hidden = true;
  $("#form-produto").reset();
  $("#disponivel").checked = true;
  $("#preview-imagem").hidden = true;
}
```

Troco `submeter` inteira:
```js
async function submeter(evento) {
  evento.preventDefault();
  const payload = {
    nome: $("#nome").value.trim(),
    descricao: $("#descricao").value.trim() || null,
    preco: $("#preco").value,
    categoria: $("#categoria").value.trim(),
    disponivel: $("#disponivel").checked,
  };
  try {
    if (editandoId) {
      await api(`/produtos/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      aviso("Produto atualizado.", "ok");
    } else {
      await api("/produtos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      aviso("Produto criado.", "ok");
    }
    sairModoEdicao();
    await carregarProdutos();
  } catch (e) {
    aviso(e.message, "erro");
  }
}
```
por:
```js
async function enviarImagem(produtoId, arquivo) {
  const dados = new FormData();
  dados.append("arquivo", arquivo);
  const resp = await fetch(`${API}/produtos/${produtoId}/imagem`, {
    method: "POST",
    body: dados,
  });
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(corpo.detail || "Falha ao enviar a imagem.");
  }
  return corpo;
}

async function submeter(evento) {
  evento.preventDefault();
  const payload = {
    nome: $("#nome").value.trim(),
    descricao: $("#descricao").value.trim() || null,
    preco: $("#preco").value,
    categoria: $("#categoria").value.trim(),
    disponivel: $("#disponivel").checked,
  };
  try {
    let produto;
    const estavaEditando = Boolean(editandoId);
    if (editandoId) {
      produto = await api(`/produtos/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      produto = await api("/produtos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    if (arquivoSelecionado) {
      await enviarImagem(produto.id, arquivoSelecionado);
    }
    aviso(estavaEditando ? "Produto atualizado." : "Produto criado.", "ok");
    sairModoEdicao();
    await carregarProdutos();
  } catch (e) {
    aviso(e.message, "erro");
  }
}
```

(Uso `fetch` direto em `enviarImagem`, não o helper `api()` — esse helper
força `Content-Type: application/json`, e upload de arquivo precisa do
`multipart/form-data` com boundary que o navegador define sozinho quando o
corpo é um `FormData`.)

Troco a linha de renderização de cada linha da tabela, dentro de
`carregarProdutos`:
```js
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.nome}</td>
      <td>${p.categoria}</td>
      <td>${brl(p.preco)}</td>
      <td>${p.disponivel ? "Sim" : "Não"}</td>
      <td></td>`;
```
por:
```js
    const tr = document.createElement("tr");
    const foto = p.imagem_url || "/images/seed/placeholder.svg";
    tr.innerHTML = `
      <td><img class="thumb" src="${foto}" alt="${p.nome}" /></td>
      <td>${p.nome}</td>
      <td>${p.categoria}</td>
      <td>${brl(p.preco)}</td>
      <td>${p.disponivel ? "Sim" : "Não"}</td>
      <td></td>`;
```

Por fim, acrescento o listener do campo de arquivo junto dos outros, no
fim do arquivo:
```js
$("#form-produto").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);
initMenu();
```
troco por:
```js
$("#form-produto").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);
$("#imagem").addEventListener("change", (e) => {
  const arquivo = e.target.files[0] ?? null;
  arquivoSelecionado = arquivo;
  const preview = $("#preview-imagem");
  if (arquivo) {
    preview.src = URL.createObjectURL(arquivo);
    preview.hidden = false;
  }
});
initMenu();
```

- [ ] **Passo 5: Teste de smoke**

Acrescento em `backend/tests/test_frontend.py`:

```python
def test_cardapio_admin_tem_campo_de_imagem(client: TestClient) -> None:
    resp = client.get("/cardapio-admin.html")
    assert 'id="imagem"' in resp.text
    assert 'id="preview-imagem"' in resp.text
```

- [ ] **Passo 6: Rodar a suíte inteira**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo (51 de antes + 1 novo = 52).

- [ ] **Passo 7: Teste manual pelo navegador**

```bash
cd backend && uvicorn app.main:app --reload
```

Abro `http://localhost:8000` e confiro: cada card do cardápio mostra a
ilustração certa. Abro `/cardapio-admin.html`: a tabela mostra a
miniatura de cada produto; crio um produto novo escolhendo uma foto no
campo de arquivo — aparece a prévia local antes de salvar, e depois de
salvar a miniatura aparece na tabela; edito um produto existente trocando
a foto; confiro que editar **sem** trocar a foto não apaga a que já
tinha. Paro o servidor e apago o `app.db` e a pasta `backend/uploads/`
gerada no teste manual.

- [ ] **Passo 8: Commit**

```bash
git add frontend/ backend/tests/test_frontend.py
git commit -m "feat: exibe e envia foto do produto no cardapio e na gestao"
```

---

## Tarefa 6: Fechamento

**Arquivos:** nenhum novo — verificação e push.

- [ ] **Passo 1: Verificação final**

Rodo: `cd backend && pytest -v`
Espero: 100% PASS (52 testes).

Confiro manualmente o fluxo completo mais uma vez: visual novo, menu
hambúrguer nas duas páginas, categoria com sugestões, fotos no cardápio e
upload funcionando.

- [ ] **Passo 2: Push da branch**

```bash
git push origin fase-2a
```

Não abro Pull Request novo — essas mudanças entram no PR #8, que já
existe e ainda está aberto.

- [ ] **Passo 3: Marcar como pronto pra revisão**

Aviso que a branch está atualizada e pronta pra revisão final de novo.

---

## Conferência: o plano cobre o design?

Revi o plano contra `design-fase-2a-visual.md` antes de começar.

**1. Cobertura do design:**
- §2 paleta/tipografia/menu hambúrguer → Tarefa 1. ✔
- §3 categoria com sugestões → Tarefa 2. ✔
- §4 banco (`imagem_url`), armazenamento, endpoint, regras de negócio,
  front-end → Tarefas 3, 4 e 5. ✔
- §5 testes (chaves da resposta, upload, formato/tamanho inválido,
  substituir imagem, excluir remove arquivo) → Tarefa 3. ✔
- §6 fora de escopo (uma foto só, sem recorte, sem imagem em pedido) →
  nenhuma tarefa extrapola isso. ✔
- §7 riscos (schema sem Alembic, `python-multipart`, uploads fora do
  volume Docker) → Tarefa 3 (instrução de apagar `app.db`, dependência
  nova) e nota no `.gitignore`. O risco do Docker eu só documentei no
  design, não resolvo no código — está anotado lá que é aceito assim. ✔

**2. Sem pontas soltas:** nenhum "TBD"/"TODO"; todo passo de código traz o
código real, incluindo as 9 ilustrações SVG inteiras. ✔

**3. Consistência de tipos:** `uploads.PRODUTOS_DIR`/`UPLOADS_ROOT`
definidos na Tarefa 3 e usados do jeito certo em `main.py` (mount) e nos
testes (`monkeypatch.setattr`). `crud.salvar_imagem_produto` tem a mesma
assinatura usada na rota nova. `atualizarListaCategorias` definida na
Tarefa 2 não muda de nome nem assinatura quando a Tarefa 5 mexe de novo em
`carregarProdutos`. ✔
