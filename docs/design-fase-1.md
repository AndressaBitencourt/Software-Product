# Software-Product — Sistema de Pedidos de Hamburgueria

## Meu documento de design — Fase 1

- **Data:** 2026-09-08
- **Repositório:** `AndressaBitencourt/Software-Product` (público)
- **Entrega:** trabalho de faculdade em 3 fases incrementais (era 5; ver seção 1)

Escrevi este documento antes de começar a codar, para fechar o escopo da
Fase 1 e registrar as decisões técnicas que tomei.

---

## 1. Visão geral do projeto

Fiz um software web para uma hamburgueria gerenciar pedidos. Não é uma página
estática: tem front-end, back-end e banco de dados, com dados dinâmicos
manipulados via API.

Dividi o projeto em **3 fases**. Cada fase adiciona funcionalidades por cima
da base da anterior, sem quebrar o que já funciona. Para cada fase eu sigo o
mesmo ciclo: design → plano → implementação → verificação.

> Histórico: eu tinha planejado o projeto em 5 fases; a faculdade depois pediu
> 3. Condensei as 4 funcionalidades que restavam nas Fases 2 e 3 (decisão de
> 2026-09-08).

| Fase | Funcionalidade | Escopo resumido |
|---|---|---|
| **1** | CRUD completo de Pedidos | Cardápio fixo (seed). Criar, listar, ver, editar e excluir pedidos. Tela web única. |
| 2 | Gestão de Cardápio **+** Fluxo do pedido | CRUD de hambúrgueres (nome, preço, categoria, disponibilidade) — o formulário de pedido passa a puxar do cardápio real. **E** ciclo de status (Recebido → Em preparo → Pronto → Entregue / Cancelado), conta detalhada, tela de cozinha por status. |
| 3 | Login e perfis **+** Relatórios / dashboard | Autenticação com papéis cliente e atendente/admin, rotas protegidas. **E** faturamento por dia, itens mais vendidos, total de pedidos, busca, filtros e gráficos simples. |

Este documento cobre **apenas a Fase 1**.

---

## 2. Stack

Escolhi ferramentas com pouca cerimônia de setup, para focar o tempo na
funcionalidade e conseguir rodar o mesmo projeto no meu Mac e num PC com
Windows.

| Camada | Escolha | Por que escolhi |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Sem etapa de build; poucas dependências; gera `/docs` (Swagger) automático para teste e demonstração. |
| ORM | SQLAlchemy 2.x | Abstrai o banco; permite trocar SQLite por Postgres em fases futuras sem reescrever as queries. |
| Banco | SQLite (arquivo `app.db`) | Zero configuração; comportamento idêntico em macOS e Windows; nenhum serviço para instalar. |
| Frontend | HTML + CSS + JavaScript puro (`fetch`) | Servido pelo próprio FastAPI como arquivos estáticos. Sem Node, sem build. Consome a API e atualiza a tela dinamicamente. |
| Testes | pytest + `TestClient` do FastAPI | Banco SQLite em memória isolado por teste. |
| Execução multiplataforma | Docker + docker-compose; alternativa `venv` + `uvicorn` documentada no README | `docker compose up` roda igual em macOS e Windows. |

**O que descartei:** Flask + templates server-side (mistura front e back e não
me dá a API de testes automática); Postgres em container já na Fase 1 (peso
extra que o escopo não pede).

---

## 3. Estrutura de pastas

```
Software-Product/
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ main.py            # instancia FastAPI, monta /api e frontend estático, cria tabelas, roda seed
│  │  ├─ database.py        # engine, SessionLocal, Base, dependência get_db
│  │  ├─ models.py          # ORM: Produto, Pedido, ItemPedido
│  │  ├─ schemas.py         # Pydantic: entrada e saída da API
│  │  ├─ crud.py            # funções de acesso a dados (sem lógica de HTTP)
│  │  ├─ seed.py            # popula o cardápio inicial se estiver vazio
│  │  └─ routers/
│  │     ├─ __init__.py
│  │     ├─ produtos.py     # somente leitura na Fase 1
│  │     └─ pedidos.py      # CRUD completo
│  ├─ tests/
│  │  ├─ conftest.py        # fixtures: app + banco em memória
│  │  ├─ test_produtos.py
│  │  └─ test_pedidos.py
│  └─ requirements.txt
├─ frontend/
│  ├─ index.html
│  ├─ styles.css
│  └─ app.js
├─ Dockerfile
├─ docker-compose.yml
├─ .dockerignore
├─ .gitignore
├─ README.md
└─ docs/
   ├─ design-fase-1.md   (este documento)
   ├─ plano-fase-1.md
   └─ backlog-fase-2.md
```

Deixei cada módulo com uma responsabilidade única: `models` descreve o banco,
`schemas` descreve o contrato da API, `crud` acessa dados, `routers` traduz
HTTP em chamadas de `crud`. Assim consigo entender e testar cada um isoladamente.

---

## 4. Modelo de dados

### Produto (cardápio — populado por seed, somente leitura na Fase 1)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | int | PK, autoincremento |
| `nome` | str(80) | obrigatório, único |
| `descricao` | str(255) | opcional |
| `preco` | Numeric(10,2) | obrigatório, > 0 |
| `categoria` | str(40) | obrigatório (ex.: Clássicos, Especiais, Acompanhamentos, Bebidas) |
| `disponivel` | bool | default `true` |

### Pedido

| Campo | Tipo | Regras |
|---|---|---|
| `id` | int | PK, autoincremento |
| `cliente_nome` | str(80) | obrigatório |
| `observacao` | str(255) | opcional |
| `status` | str(20) | default `"recebido"` — fixo na Fase 1; ciclo completo entra na Fase 2 |
| `criado_em` | datetime | preenchido na criação (UTC) |
| `atualizado_em` | datetime | atualizado a cada alteração (UTC) |
| `total` | — | **não é coluna**; calculado como soma dos `subtotal` dos itens |

### ItemPedido

| Campo | Tipo | Regras |
|---|---|---|
| `id` | int | PK, autoincremento |
| `pedido_id` | FK → Pedido | `ON DELETE CASCADE` |
| `produto_id` | FK → Produto | obrigatório |
| `quantidade` | int | obrigatório, ≥ 1 |
| `preco_unitario` | Numeric(10,2) | snapshot do `preco` do produto no momento do pedido |
| `subtotal` | — | **não é coluna**; `quantidade * preco_unitario` |

Relação: `Pedido.itens` um-para-muitos, `cascade="all, delete-orphan"`.
O snapshot de `preco_unitario` garante que alterar o cardápio depois (Fase 2)
não muda o valor de pedidos antigos.

### Seed do cardápio

8 itens fixos criados na primeira execução se a tabela `produto` estiver
vazia. Exemplos: X-Salada, X-Bacon, X-Tudo, X-Vegetariano (Clássicos/Especiais),
Batata Frita, Onion Rings (Acompanhamentos), Refrigerante, Suco (Bebidas).
Valores definidos no código de `seed.py`.

---

## 5. API (base `/api`)

Respostas em JSON. Erros no formato padrão do FastAPI: `{"detail": "..."}`.

| Método | Rota | Descrição | Códigos |
|---|---|---|---|
| `GET` | `/api/health` | Checagem rápida do serviço | 200 |
| `GET` | `/api/produtos` | Lista o cardápio. `?incluir_indisponiveis=true` opcional | 200 |
| `GET` | `/api/produtos/{id}` | Detalhe de um produto | 200, 404 |
| `POST` | `/api/pedidos` | Cria um pedido | 201, 400, 422 |
| `GET` | `/api/pedidos` | Lista pedidos (resumo) | 200 |
| `GET` | `/api/pedidos/{id}` | Detalhe do pedido com itens | 200, 404 |
| `PUT` | `/api/pedidos/{id}` | Substitui nome, observação e itens; recalcula total | 200, 400, 404, 422 |
| `DELETE` | `/api/pedidos/{id}` | Exclui o pedido e seus itens (cascade) | 204, 404 |

### Contratos

**Criar / atualizar pedido (request)**

```json
{
  "cliente_nome": "Maria",
  "observacao": "sem cebola",
  "itens": [
    { "produto_id": 1, "quantidade": 2 },
    { "produto_id": 5, "quantidade": 1 }
  ]
}
```

**Pedido (response detalhada)**

```json
{
  "id": 10,
  "cliente_nome": "Maria",
  "observacao": "sem cebola",
  "status": "recebido",
  "criado_em": "2026-09-08T14:30:00Z",
  "atualizado_em": "2026-09-08T14:30:00Z",
  "itens": [
    { "id": 21, "produto_id": 1, "produto_nome": "X-Salada",
      "quantidade": 2, "preco_unitario": "18.00", "subtotal": "36.00" },
    { "id": 22, "produto_id": 5, "produto_nome": "Batata Frita",
      "quantidade": 1, "preco_unitario": "12.00", "subtotal": "12.00" }
  ],
  "total": "48.00"
}
```

**Lista de pedidos (response resumida):** `id`, `cliente_nome`, `status`,
`quantidade_itens`, `total`, `criado_em`.

### Regras de negócio (validadas no backend)

- Pedido precisa ter **pelo menos 1 item** → senão `400`.
- `quantidade` de cada item ≥ 1 → senão `422` (Pydantic).
- Todo `produto_id` deve existir → senão `400` com a mensagem indicando o id.
- Produto com `disponivel = false` não pode entrar em pedido novo → `400`.
- `preco_unitario` e `total` são sempre calculados pelo servidor; qualquer
  valor de preço enviado pelo cliente é ignorado.
- `PUT` substitui a lista de itens inteira (remove os antigos, cria os novos)
  e atualiza `atualizado_em`.

---

## 6. Frontend — página única

`index.html` servido em `/`. Título: **"Hamburgueria — Pedidos"**.
Três seções na mesma página, todas atualizadas via `fetch` sem recarregar:

1. **Cardápio** — cards com nome, descrição, preço e categoria. Botão
   "Adicionar" joga o item no carrinho do formulário.
2. **Novo pedido / Editar pedido** — campo nome do cliente, campo observação,
   carrinho com quantidade editável por item, subtotal por linha, total geral,
   botão "Fazer pedido" (POST) ou "Salvar alterações" (PUT quando em edição).
   Botão "Cancelar edição" volta ao modo criação.
3. **Pedidos** — lista de todos os pedidos (cliente, nº de itens, total,
   status, data). Cada linha tem:
   - **Ver** — expande os itens do pedido.
   - **Editar** — carrega o pedido na seção 2 em modo edição.
   - **Excluir** — pede confirmação e faz `DELETE`, depois recarrega a lista.

Toda chamada trata `response.ok === false` e mostra a mensagem de `detail`
em uma faixa de aviso no topo. Sucesso mostra confirmação curta.
CSS próprio, tema simples de hamburgueria, layout responsivo básico
(coluna única no celular).

`app.js` concentra: funções de acesso à API, estado do carrinho em memória,
e renderização das três seções.

---

## 7. Tratamento de erros

- **Validação de formato:** Pydantic → `422` automático com detalhe do campo.
- **Regra de negócio:** `HTTPException` com status e mensagem clara em
  português (`400` / `404`).
- **Banco:** uma `Session` por requisição via dependência `get_db`
  (`try / finally` fecha; exceção faz `rollback`).
- **Frontend:** helper único de `fetch` que lê `detail` em respostas de erro
  e exibe para o usuário; nunca falha silenciosamente.

---

## 8. Testes (pytest)

Fixture cria um app novo com banco SQLite **em memória** por teste, com o
seed carregado. `TestClient` para chamadas HTTP.

| # | Caso | Esperado |
|---|---|---|
| 1 | `GET /api/health` | 200, `{"status": "ok"}` |
| 2 | `GET /api/produtos` | 200, retorna os 8 itens do seed |
| 3 | `GET /api/produtos/{id}` inexistente | 404 |
| 4 | `POST /api/pedidos` válido com 2 itens | 201; `total` = soma correta; `preco_unitario` = preço do seed |
| 5 | `POST` sem itens (`"itens": []`) | 400 |
| 6 | `POST` com `produto_id` inexistente | 400 |
| 7 | `POST` com `quantidade: 0` | 422 |
| 8 | `POST` com produto marcado indisponível | 400 |
| 9 | `GET /api/pedidos` após criar 2 pedidos | 200, lista com 2, campos de resumo corretos |
| 10 | `GET /api/pedidos/{id}` existente | 200, itens e total corretos |
| 11 | `GET /api/pedidos/{id}` inexistente | 404 |
| 12 | `PUT /api/pedidos/{id}` alterando itens | 200; `total` recalculado; `atualizado_em` muda |
| 13 | `PUT` em pedido inexistente | 404 |
| 14 | `DELETE /api/pedidos/{id}` | 204; some da listagem |
| 15 | `DELETE` remove os `ItemPedido` associados (cascade) | nenhum item órfão no banco |
| 16 | `DELETE` em pedido inexistente | 404 |

**Critério de pronto da Fase 1:** os 16 testes passando em macOS, mais
verificação manual da página (criar, ver, editar e excluir um pedido pela UI)
e `GET /docs` acessível.

---

## 9. Execução e portabilidade macOS / Windows

**Com Docker (recomendado para o deploy):**

```
docker compose up --build
# app em http://localhost:8000  (UI em /, API em /api, docs em /docs)
```

`Dockerfile` baseado em `python:3.12-slim`, instala `requirements.txt`, roda
`uvicorn app.main:app --host 0.0.0.0 --port 8000`. `docker-compose.yml` mapeia
a porta `8000` e um volume para persistir `app.db`. Comportamento idêntico nos
dois sistemas operacionais.

**Sem Docker:**

```
cd backend
python -m venv .venv
# macOS:   source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

SQLite não exige nada instalado. Caminho do banco montado com `pathlib` para
não depender de separador de path do SO.

**`.gitignore`:** `__pycache__/`, `*.pyc`, `.venv/`, `*.db`, `.pytest_cache/`,
`.DS_Store`, `.env`.

---

## 10. Fora de escopo na Fase 1 (entra depois)

- CRUD de produtos pela API/UI (Fase 2).
- Mudança de status do pedido e tela de cozinha (Fase 2).
- Autenticação, sessões e papéis (Fase 3).
- Relatórios e gráficos (Fase 3).
- Paginação da lista de pedidos, migrações de schema (Alembic), CI.

---

## 11. Riscos e decisões em aberto

| Item | Decisão |
|---|---|
| Precisão monetária | `Numeric(10,2)` no banco; `Decimal` no backend; string no JSON para evitar erro de float. |
| Concorrência | Não tratada na Fase 1 (uso single-user de faculdade). SQLite serializa escritas. |
| Persistência do `app.db` em Docker | Volume nomeado no compose; documentado que apagar o volume zera os dados. |
| Deploy final (onde hospedar) | Em aberto; para a entrega, `docker compose up` local atende. Reavaliar em fase posterior se o professor exigir URL pública. |
