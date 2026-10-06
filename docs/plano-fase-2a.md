# Fase 2a — Gestão de Cardápio — Plano de implementação

> Uso o skill `subagent-driven-development` (recomendado) ou `executing-plans`
> pra seguir esse plano tarefa por tarefa. Os passos usam `- [ ]` pra eu
> marcar conforme termino.

**Objetivo:** tornar o cardápio gerenciável — criar, editar, marcar
disponível/indisponível e excluir produtos — sem mexer direto no banco, e
corrigir o nome do produto nos pedidos pra ser uma "foto" do momento (igual
já é o preço).

**Arquitetura:** sigo exatamente as mesmas camadas da Fase 1
(`models` → `schemas` → `crud` → `serializers`/routers), só adicionando o que
falta pra CRUD completo de `Produto`. No front, crio uma página nova
(`cardapio-admin.html` + `admin.js`) separada da tela de pedidos.

**Stack:** a mesma da Fase 1 — Python 3.12, FastAPI, SQLAlchemy 2.x, SQLite,
Pydantic v2, pytest + httpx, sem Docker/Node necessário pra rodar os testes.

## Regras que sigo

- Python **3.12**; back-end em `backend/`, front em `frontend/`.
- Banco: **SQLite** via SQLAlchemy ORM. Nada de SQL cru fora do ORM.
- Dinheiro: coluna `Numeric(10, 2)`; `Decimal` no Python; **string com 2
  casas** no JSON (reaproveito o tipo `Money` que já existe em `schemas.py`).
- API sob o prefixo `/api`. Erros no formato `{"detail": "<mensagem em
  português>"}`.
- `preco` do produto é sempre o que vem no corpo da requisição (preço > 0,
  validado pelo Pydantic); já `preco_unitario` e `produto_nome` num
  `ItemPedido` continuam sendo *sempre* a foto do momento do pedido, nunca o
  valor atual do produto.
- Todo o trabalho dessa fase vai na branch `fase-2a` (criada na Tarefa 1),
  um commit por passo de "Commit".
- Cada teste roda com: `cd backend && pytest`.
- Escopo travado: **só o que está neste plano** — CRUD de produto e a
  correção do snapshot de nome. Sem mudança de status de pedido, sem conta
  detalhada nova, sem tela de cozinha (isso é a Fase 2b, com seu próprio
  plano). Sem login (Fase 3).

---

## Estrutura de arquivos

```
backend/
  app/
    models.py            # ItemPedido ganha o campo produto_nome
    schemas.py            # ProdutoIn novo
    crud.py                # criar_produto, atualizar_produto, excluir_produto
    serializers.py        # usa item.produto_nome em vez de item.produto.nome
    routers/
      produtos.py          # ganha POST, PUT, DELETE
  tests/
    test_produtos.py       # testes do CRUD de produto
    test_pedidos.py        # teste do snapshot de produto_nome
    test_frontend.py       # smoke test da pagina nova
frontend/
  index.html               # ganha um link de navegação pro cardápio
  cardapio-admin.html       # pagina nova
  admin.js                  # pagina nova
  styles.css                # pequenos ajustes (checkbox, nav)
```

---

## Tarefa 1: Snapshot do nome do produto em `ItemPedido`

**Arquivos:**
- Modifico: `backend/app/models.py`
- Modifico: `backend/app/crud.py`
- Modifico: `backend/app/serializers.py`
- Teste: `backend/tests/test_pedidos.py`

**Interfaces:**
- Consome: `models.ItemPedido`, `crud._montar_itens` (já existentes).
- Produz: `ItemPedido.produto_nome: str` — passa a existir no banco e é
  preenchido em `_montar_itens`. A partir daqui, `serializers.py` lê o nome
  do item por esse campo, não mais por `item.produto.nome`.

- [ ] **Passo 1: Criar a branch de trabalho**

```bash
git checkout -b fase-2a
```

- [ ] **Passo 2: Escrever o teste que falha**

Acrescento ao fim de `backend/tests/test_pedidos.py`:

```python
def test_produto_nome_e_snapshot(client: TestClient, db_session) -> None:
    from app import models

    criado = client.post("/api/pedidos", json=PEDIDO_VALIDO).json()
    db_session.get(models.Produto, 1).nome = "X-Salada Supreme"
    db_session.commit()

    depois = client.get(f"/api/pedidos/{criado['id']}").json()
    assert depois["itens"][0]["produto_nome"] == "X-Salada"
```

- [ ] **Passo 3: Rodar e ver falhar**

Rodo: `cd backend && pytest tests/test_pedidos.py::test_produto_nome_e_snapshot -v`
Espero: FAIL — `AssertionError: assert 'X-Salada Supreme' == 'X-Salada'`. Essa
falha prova o bug: hoje o nome vem ao vivo de `item.produto.nome`, então
renomear o produto reescreve o nome em pedidos antigos.

- [ ] **Passo 4: Adicionar a coluna em `models.py`**

Em `backend/app/models.py`, na classe `ItemPedido`, troco:

```python
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    quantidade: Mapped[int] = mapped_column()
```

por:

```python
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    produto_nome: Mapped[str] = mapped_column(String(80))
    quantidade: Mapped[int] = mapped_column()
```

(`String` já está importado no topo do arquivo.)

- [ ] **Passo 5: Preencher o snapshot em `crud.py`**

Em `backend/app/crud.py`, na função `_montar_itens`, troco:

```python
        itens.append(
            models.ItemPedido(
                produto_id=produto.id,
                quantidade=entrada.quantidade,
                preco_unitario=produto.preco,
            )
        )
```

por:

```python
        itens.append(
            models.ItemPedido(
                produto_id=produto.id,
                produto_nome=produto.nome,
                quantidade=entrada.quantidade,
                preco_unitario=produto.preco,
            )
        )
```

- [ ] **Passo 6: Usar o snapshot em `serializers.py`**

Em `backend/app/serializers.py`, dentro de `pedido_para_out`, troco:

```python
            produto_nome=item.produto.nome,
```

por:

```python
            produto_nome=item.produto_nome,
```

- [ ] **Passo 7: Apagar o banco de teste manual e rodar a suíte inteira**

Como `produto_nome` é coluna nova, apago `backend/app.db` se existir (ele é
recriado sozinho — não precisa em testes automatizados, que usam banco em
memória, só se eu for testar manualmente pelo navegador depois).

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo (as 29 testes existentes + o novo).

- [ ] **Passo 8: Commit**

```bash
git add backend/app/models.py backend/app/crud.py backend/app/serializers.py backend/tests/test_pedidos.py
git commit -m "fix: produto_nome vira snapshot em ItemPedido, igual preco_unitario"
```

---

## Tarefa 2: Criar produto — `POST /api/produtos`

**Arquivos:**
- Modifico: `backend/app/schemas.py`
- Modifico: `backend/app/crud.py`
- Modifico: `backend/app/routers/produtos.py`
- Teste: `backend/tests/test_produtos.py`

**Interfaces:**
- Consome: `crud.RegraNegocioError` (já existe).
- Produz: `schemas.ProdutoIn` (nome, descricao, preco, categoria,
  disponivel) — usado também nas Tarefas 3 e 4 (PUT reaproveita o mesmo
  schema). `crud.criar_produto(db, dados: schemas.ProdutoIn) ->
  models.Produto`.

- [ ] **Passo 1: Escrever os testes que falham**

Acrescento ao fim de `backend/tests/test_produtos.py`:

```python
PRODUTO_NOVO = {
    "nome": "X-Frango",
    "descricao": "Frango grelhado, queijo, alface e maionese",
    "preco": "21.50",
    "categoria": "Clássicos",
    "disponivel": True,
}


def test_criar_produto_valido(client: TestClient) -> None:
    resp = client.post("/api/produtos", json=PRODUTO_NOVO)
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["nome"] == "X-Frango"
    assert corpo["preco"] == "21.50"
    assert corpo["disponivel"] is True

    listados = client.get("/api/produtos").json()
    assert len(listados) == 9


def test_criar_produto_nome_duplicado_400(client: TestClient) -> None:
    resp = client.post(
        "/api/produtos",
        json={**PRODUTO_NOVO, "nome": "X-Salada"},
    )
    assert resp.status_code == 400
    assert "X-Salada" in resp.json()["detail"]


def test_criar_produto_preco_invalido_422(client: TestClient) -> None:
    resp = client.post("/api/produtos", json={**PRODUTO_NOVO, "preco": "0"})
    assert resp.status_code == 422
```

- [ ] **Passo 2: Rodar e ver falhar**

Rodo: `cd backend && pytest tests/test_produtos.py -k criar_produto -v`
Espero: FAIL — `AttributeError` (schema não existe) ou `405` (rota não existe).

- [ ] **Passo 3: `ProdutoIn` em `schemas.py`**

Acrescento em `backend/app/schemas.py`, depois da classe `ProdutoOut`:

```python
class ProdutoIn(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    preco: Decimal = Field(gt=0)
    categoria: str = Field(min_length=1, max_length=40)
    disponivel: bool = True
```

(`Decimal` e `Field` já estão importados no topo do arquivo.)

- [ ] **Passo 4: `criar_produto` em `crud.py`**

Acrescento em `backend/app/crud.py`, depois de `obter_produto`:

```python
def criar_produto(db: Session, dados: schemas.ProdutoIn) -> models.Produto:
    existente = db.scalar(
        select(models.Produto).where(models.Produto.nome == dados.nome)
    )
    if existente is not None:
        raise RegraNegocioError(f"Já existe um produto chamado '{dados.nome}'.")
    produto = models.Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        categoria=dados.categoria,
        disponivel=dados.disponivel,
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto
```

- [ ] **Passo 5: Rota `POST` em `routers/produtos.py`**

No topo do arquivo, troco o import:

```python
from fastapi import APIRouter, Depends, HTTPException
```

por (acrescenta `status`):

```python
from fastapi import APIRouter, Depends, HTTPException, status
```

E, enquanto mexo no arquivo, corrijo a anotação de retorno "pelada" da rota
`listar` que já existia (de `-> list:` para `-> list[schemas.ProdutoOut]:`):

```python
@router.get("", response_model=list[schemas.ProdutoOut])
def listar(
    incluir_indisponiveis: bool = False, db: Session = Depends(get_db)
) -> list[schemas.ProdutoOut]:
    return crud.listar_produtos(db, incluir_indisponiveis)
```

Acrescento, no fim do arquivo:

```python
@router.post(
    "", response_model=schemas.ProdutoOut, status_code=status.HTTP_201_CREATED
)
def criar(dados: schemas.ProdutoIn, db: Session = Depends(get_db)):
    try:
        produto = crud.criar_produto(db, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    return produto
```

- [ ] **Passo 6: Rodar e ver passar**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo.

- [ ] **Passo 7: Commit**

```bash
git add backend/app/schemas.py backend/app/crud.py backend/app/routers/produtos.py backend/tests/test_produtos.py
git commit -m "feat: criacao de produto via POST /api/produtos"
```

---

## Tarefa 3: Editar produto — `PUT /api/produtos/{id}`

**Arquivos:**
- Modifico: `backend/app/crud.py`
- Modifico: `backend/app/routers/produtos.py`
- Teste: `backend/tests/test_produtos.py`

**Interfaces:**
- Consome: `schemas.ProdutoIn` (Tarefa 2), `crud.RegraNegocioError`.
- Produz: `crud.atualizar_produto(db, produto_id: int, dados:
  schemas.ProdutoIn) -> models.Produto | None` (`None` = produto não existe).

- [ ] **Passo 1: Escrever os testes que falham**

Acrescento ao fim de `backend/tests/test_produtos.py`:

```python
def test_editar_produto(client: TestClient) -> None:
    resp = client.put(
        "/api/produtos/1",
        json={
            "nome": "X-Salada Supreme",
            "descricao": "Hambúrguer duplo, queijo, alface, tomate e maionese",
            "preco": "20.00",
            "categoria": "Clássicos",
            "disponivel": False,
        },
    )
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["nome"] == "X-Salada Supreme"
    assert corpo["preco"] == "20.00"
    assert corpo["disponivel"] is False


def test_editar_produto_nome_de_outro_400(client: TestClient) -> None:
    resp = client.put(
        "/api/produtos/1",
        json={**PRODUTO_NOVO, "nome": "X-Bacon"},
    )
    assert resp.status_code == 400
    assert "X-Bacon" in resp.json()["detail"]


def test_editar_produto_inexistente_404(client: TestClient) -> None:
    resp = client.put("/api/produtos/999", json=PRODUTO_NOVO)
    assert resp.status_code == 404
```

- [ ] **Passo 2: Rodar e ver falhar**

Rodo: `cd backend && pytest tests/test_produtos.py -k editar_produto -v`
Espero: FAIL — `405` (rota `PUT` não existe).

- [ ] **Passo 3: `atualizar_produto` em `crud.py`**

Acrescento em `backend/app/crud.py`, depois de `criar_produto`:

```python
def atualizar_produto(
    db: Session, produto_id: int, dados: schemas.ProdutoIn
) -> models.Produto | None:
    produto = db.get(models.Produto, produto_id)
    if produto is None:
        return None
    conflito = db.scalar(
        select(models.Produto).where(
            models.Produto.nome == dados.nome, models.Produto.id != produto_id
        )
    )
    if conflito is not None:
        raise RegraNegocioError(f"Já existe um produto chamado '{dados.nome}'.")
    produto.nome = dados.nome
    produto.descricao = dados.descricao
    produto.preco = dados.preco
    produto.categoria = dados.categoria
    produto.disponivel = dados.disponivel
    db.commit()
    db.refresh(produto)
    return produto
```

- [ ] **Passo 4: Rota `PUT` em `routers/produtos.py`**

Acrescento no fim do arquivo:

```python
@router.put("/{produto_id}", response_model=schemas.ProdutoOut)
def atualizar(
    produto_id: int, dados: schemas.ProdutoIn, db: Session = Depends(get_db)
):
    try:
        produto = crud.atualizar_produto(db, produto_id, dados)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto
```

- [ ] **Passo 5: Rodar e ver passar**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo.

- [ ] **Passo 6: Commit**

```bash
git add backend/app/crud.py backend/app/routers/produtos.py backend/tests/test_produtos.py
git commit -m "feat: edicao de produto via PUT /api/produtos/{id}"
```

---

## Tarefa 4: Excluir produto — `DELETE /api/produtos/{id}`

**Arquivos:**
- Modifico: `backend/app/crud.py`
- Modifico: `backend/app/routers/produtos.py`
- Teste: `backend/tests/test_produtos.py`

**Interfaces:**
- Consome: `crud.RegraNegocioError`.
- Produz: `crud.excluir_produto(db, produto_id: int) -> bool` (`False` =
  produto não existe; levanta `RegraNegocioError` se o produto está
  referenciado em algum `ItemPedido`).

- [ ] **Passo 1: Escrever os testes que falham**

Acrescento ao fim de `backend/tests/test_produtos.py`:

```python
def test_excluir_produto_sem_pedido(client: TestClient) -> None:
    criado = client.post("/api/produtos", json=PRODUTO_NOVO).json()

    resp = client.delete(f"/api/produtos/{criado['id']}")
    assert resp.status_code == 204

    assert client.get(f"/api/produtos/{criado['id']}").status_code == 404


def test_excluir_produto_com_pedido_400(client: TestClient) -> None:
    resp_pedido = client.post(
        "/api/pedidos",
        json={"cliente_nome": "Ana", "itens": [{"produto_id": 1, "quantidade": 1}]},
    )
    assert resp_pedido.status_code == 201

    resp = client.delete("/api/produtos/1")
    assert resp.status_code == 400
    assert "pedidos" in resp.json()["detail"]
    assert client.get("/api/produtos/1").status_code == 200


def test_excluir_produto_inexistente_404(client: TestClient) -> None:
    resp = client.delete("/api/produtos/999")
    assert resp.status_code == 404
```

- [ ] **Passo 2: Rodar e ver falhar**

Rodo: `cd backend && pytest tests/test_produtos.py -k excluir_produto -v`
Espero: FAIL — `405` (rota `DELETE` não existe).

- [ ] **Passo 3: `excluir_produto` em `crud.py`**

No topo de `backend/app/crud.py`, troco o import:

```python
from sqlalchemy import select
```

por (acrescenta `func`):

```python
from sqlalchemy import func, select
```

Acrescento no fim do arquivo:

```python
def excluir_produto(db: Session, produto_id: int) -> bool:
    produto = db.get(models.Produto, produto_id)
    if produto is None:
        return False
    em_uso = db.scalar(
        select(func.count())
        .select_from(models.ItemPedido)
        .where(models.ItemPedido.produto_id == produto_id)
    )
    if em_uso:
        raise RegraNegocioError(
            "Não é possível excluir — esse produto já aparece em pedidos. "
            "Marque como indisponível em vez de excluir."
        )
    db.delete(produto)
    db.commit()
    return True
```

- [ ] **Passo 4: Rota `DELETE` em `routers/produtos.py`**

Acrescento no fim do arquivo:

```python
@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(produto_id: int, db: Session = Depends(get_db)):
    try:
        encontrou = crud.excluir_produto(db, produto_id)
    except crud.RegraNegocioError as erro:
        raise HTTPException(status_code=400, detail=erro.mensagem)
    if not encontrou:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
```

- [ ] **Passo 5: Rodar a suíte inteira e conferir a cobertura de produtos**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo. Confiro que o conjunto de testes do CRUD de produto
está completo: criar (válido, nome duplicado, preço inválido), editar
(válido, nome de outro, inexistente), excluir (sem pedido, com pedido
bloqueado, inexistente), mais o snapshot de nome da Tarefa 1.

- [ ] **Passo 6: Commit**

```bash
git add backend/app/crud.py backend/app/routers/produtos.py backend/tests/test_produtos.py
git commit -m "feat: exclusao de produto com bloqueio se ja usado em pedido"
```

---

## Tarefa 5: Front-end — página `cardapio-admin.html`

**Arquivos:**
- Cria: `frontend/cardapio-admin.html`
- Cria: `frontend/admin.js`
- Modifico: `frontend/index.html` (link de navegação)
- Modifico: `frontend/styles.css` (checkbox e nav)
- Teste: `backend/tests/test_frontend.py`

**Interfaces:**
- Consome: a API de produtos já pronta (Tarefas 2–4): `POST /api/produtos`,
  `PUT /api/produtos/{id}`, `DELETE /api/produtos/{id}`, `GET
  /api/produtos?incluir_indisponiveis=true` (já existia desde a Fase 1).
- Produz: página em `/cardapio-admin.html` que lista, cria, edita e exclui
  produtos via `fetch`, sem recarregar.

- [ ] **Passo 1: Teste que falha (smoke do estático)**

Acrescento ao fim de `backend/tests/test_frontend.py`:

```python
def test_cardapio_admin_serve_a_pagina(client: TestClient) -> None:
    resp = client.get("/cardapio-admin.html")
    assert resp.status_code == 200
    assert "Cardápio" in resp.text
    assert "admin.js" in resp.text
```

- [ ] **Passo 2: Rodar e ver falhar**

Rodo: `cd backend && pytest tests/test_frontend.py -v`
Espero: FAIL — `404` (`cardapio-admin.html` ainda não existe).

- [ ] **Passo 3: `frontend/cardapio-admin.html`**

```html
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hamburgueria — Cardápio</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header>
    <h1>🍔 Hamburgueria — Cardápio</h1>
    <nav><a href="/">Pedidos</a></nav>
  </header>

  <div id="aviso" class="aviso" hidden></div>

  <main>
    <section id="secao-form">
      <h2 id="form-titulo">Novo produto</h2>
      <form id="form-produto">
        <label>Nome
          <input type="text" id="nome" maxlength="80" required />
        </label>
        <label>Descrição
          <input type="text" id="descricao" maxlength="255" />
        </label>
        <label>Preço (R$)
          <input type="number" id="preco" min="0.01" step="0.01" required />
        </label>
        <label>Categoria
          <input type="text" id="categoria" maxlength="40" required />
        </label>
        <label>
          <input type="checkbox" id="disponivel" checked />
          Disponível
        </label>

        <div class="acoes">
          <button type="submit" id="btn-salvar">Salvar produto</button>
          <button type="button" id="btn-cancelar" hidden>Cancelar edição</button>
        </div>
      </form>
    </section>

    <section id="secao-produtos">
      <h2>Produtos</h2>
      <table>
        <thead>
          <tr>
            <th>Nome</th><th>Categoria</th><th>Preço</th>
            <th>Disponível</th><th></th>
          </tr>
        </thead>
        <tbody id="lista-produtos"></tbody>
      </table>
      <p id="produtos-vazio" hidden>Nenhum produto cadastrado.</p>
    </section>
  </main>

  <script src="admin.js"></script>
</body>
</html>
```

- [ ] **Passo 4: `frontend/admin.js`**

```javascript
"use strict";

const API = "/api";
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

function sairModoEdicao() {
  editandoId = null;
  $("#form-titulo").textContent = "Novo produto";
  $("#btn-salvar").textContent = "Salvar produto";
  $("#btn-cancelar").hidden = true;
  $("#form-produto").reset();
  $("#disponivel").checked = true;
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

async function carregarProdutos() {
  const produtos = await api("/produtos?incluir_indisponiveis=true");
  const tbody = $("#lista-produtos");
  tbody.innerHTML = "";
  $("#produtos-vazio").hidden = produtos.length > 0;
  for (const p of produtos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.nome}</td>
      <td>${p.categoria}</td>
      <td>${brl(p.preco)}</td>
      <td>${p.disponivel ? "Sim" : "Não"}</td>
      <td></td>`;
    const acoes = tr.lastElementChild;

    const bEditar = document.createElement("button");
    bEditar.textContent = "Editar";
    bEditar.addEventListener("click", () => entrarModoEdicao(p));

    const bExcluir = document.createElement("button");
    bExcluir.textContent = "Excluir";
    bExcluir.className = "perigo";
    bExcluir.addEventListener("click", async () => {
      if (!confirm(`Excluir o produto "${p.nome}"?`)) return;
      try {
        await api(`/produtos/${p.id}`, { method: "DELETE" });
        aviso("Produto excluído.", "ok");
        await carregarProdutos();
      } catch (e) {
        aviso(e.message, "erro");
      }
    });

    acoes.append(bEditar, bExcluir);
    tbody.appendChild(tr);
  }
}

$("#form-produto").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);

(async function iniciar() {
  try {
    await carregarProdutos();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
```

- [ ] **Passo 5: Link de navegação em `frontend/index.html`**

Dentro de `<header>`, troco:

```html
  <header>
    <h1>🍔 Hamburgueria — Pedidos</h1>
  </header>
```

por:

```html
  <header>
    <h1>🍔 Hamburgueria — Pedidos</h1>
    <nav><a href="/cardapio-admin.html">Gerenciar cardápio</a></nav>
  </header>
```

- [ ] **Passo 6: Ajustes em `frontend/styles.css`**

Acrescento no fim do arquivo:

```css
header nav { margin-top: 6px; }
header nav a {
  color: #fff;
  text-decoration: underline;
  font-size: 0.9rem;
}
input[type="checkbox"] {
  display: inline-block;
  width: auto;
  margin-right: 6px;
}
```

(Sem isso, o seletor `form input` que já existe deixaria o checkbox
esticado `width: 100%`, do tamanho da tela inteira.)

- [ ] **Passo 7: Rodar a suíte**

Rodo: `cd backend && pytest -v`
Espero: PASS em tudo.

- [ ] **Passo 8: Teste manual pelo navegador**

```bash
cd backend && uvicorn app.main:app --reload
```

Abro `http://localhost:8000/cardapio-admin.html` e confiro:
- a tabela lista os produtos do seed (inclusive se eu marcar algum
  indisponível, ele continua aparecendo aqui — diferente da tela de pedidos);
- criar um produto novo aparece na tabela e no cardápio da tela de pedidos;
- editar um produto (inclusive desmarcar "Disponível") reflete na tabela;
- excluir um produto **sem** pedido associado funciona;
- tentar excluir um produto **com** pedido associado mostra o erro em
  vermelho e o produto continua na tabela;
- o link "Gerenciar cardápio" (em `/`) e "Pedidos" (na página de cardápio)
  navegam entre as duas páginas.

Paro o servidor (`Ctrl+C`) e apago o `backend/app.db` gerado.

- [ ] **Passo 9: Commit**

```bash
git add frontend/ backend/tests/test_frontend.py
git commit -m "feat: pagina de gestao de cardapio (criar, editar, excluir produto)"
```

---

## Tarefa 6: Fechamento da Fase 2a

**Arquivos:** nenhum novo — verificação e integração.

- [ ] **Passo 1: Verificação final**

Rodo: `cd backend && pytest -v`
Espero: 100% PASS.

Confiro manualmente uma última vez pelo navegador o fluxo completo: cardápio
(incluir/editar/excluir produto) e pedidos (continuam funcionando com o
cardápio agora editável).

- [ ] **Passo 2: Push da branch**

```bash
git push -u origin fase-2a
```

- [ ] **Passo 3: Abrir o Pull Request**

```bash
gh pr create --base main --head fase-2a \
  --title "Fase 2a — Gestão de cardápio" \
  --body "$(cat <<'EOF'
## Fase 2a — Gestão de Cardápio

Primeiro ciclo da Fase 2 (dividi em 2a/2b pra manter os PRs revisáveis).

### O que tem
- CRUD completo de produtos: `POST`/`PUT`/`DELETE` em `/api/produtos`
- Corrige um bug que o cardápio editável ia expor: `produto_nome` agora é
  uma foto do momento do pedido em `ItemPedido`, igual já é o `preco_unitario`
- Exclusão de produto bloqueada se ele já aparece em algum pedido (sugere
  marcar como indisponível)
- Página nova `cardapio-admin.html` pra gerenciar o cardápio, separada da
  tela de pedidos
- Testes novos cobrindo o CRUD de produto e o snapshot de nome

### Como testar
`cd backend && pip install -r requirements.txt && pytest -v`
ou `uvicorn app.main:app --reload` e abrir `/cardapio-admin.html`

### Fora desse PR
Fluxo de status do pedido, conta detalhada e tela de cozinha ficam pro
próximo ciclo (Fase 2b).
EOF
)"
```

- [ ] **Passo 4: Marcar como pronta pra revisão/merge**

Depois de mergear na `main`, desenho a Fase 2b a partir dela.

---

## Conferência: o plano cobre o design?

Revi o plano contra `design-fase-2a.md` antes de começar a implementar.

**1. Cobertura do design:**
- §2 problema do nome ao vivo → Tarefa 1. ✔
- §3 modelo de dados (`produto_nome`, regra de exclusão bloqueada) → Tarefas 1 e 4. ✔
- §4 endpoints (`POST`/`PUT`/`DELETE` em `/api/produtos`) → Tarefas 2, 3, 4. ✔
- §4 regras de negócio (nome único, preço > 0, exclusão bloqueada, 404s) → Tarefas 2, 3, 4. ✔
- §5 front-end (`cardapio-admin.html` separado, navegação, duplicação pequena de helpers) → Tarefa 5. ✔
- §6 tratamento de erros → mesmo padrão `RegraNegocioError`/Pydantic já usado nas Tarefas 2–4. ✔
- §7 testes → distribuídos nas Tarefas 1–4, mais o smoke da página na Tarefa 5. ✔
- §9 risco do schema sem Alembic → anotado nos Passos 7 (Tarefa 1) e 8 (Tarefa 5), lembrando de apagar `app.db`. ✔

**2. Sem pontas soltas:** nenhum "TBD"/"TODO"; todo passo de código traz o
código real. ✔

**3. Consistência de tipos:** `schemas.ProdutoIn` (Tarefa 2) é o mesmo tipo
usado em `criar_produto` e `atualizar_produto` (Tarefas 2 e 3) e nas rotas
`POST`/`PUT` (mesmas tarefas). `crud.excluir_produto` (Tarefa 4) segue o
mesmo formato de retorno (`bool` + `RegraNegocioError`) que
`crud.excluir_pedido` já usava na Fase 1. ✔
