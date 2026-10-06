# Software-Product — Sistema de Pedidos de Hamburgueria

## Meu documento de design — Fase 2a (Gestão de Cardápio)

- **Data:** 2026-10-06
- **Repositório:** `AndressaBitencourt/Software-Product` (público), branch a
  partir de `main` (já com a Fase 1 mergeada)
- **Entrega:** primeiro ciclo da Fase 2 — dividi a Fase 2 em dois ciclos
  (2a e 2b) pra manter cada PR revisável. Esse aqui cobre só o **cardápio**.

Escrevi este documento antes de codar, pra fechar o escopo da Fase 2a e
registrar as decisões técnicas.

---

## 1. Visão geral

Na Fase 1 o cardápio era fixo (populado por seed, só leitura). Nessa etapa
ele vira **gerenciável**: dá pra cadastrar, editar, marcar
disponível/indisponível e excluir hambúrgueres pela própria aplicação — sem
mexer direto no banco.

Fase 2 completa (do roadmap) junta duas funcionalidades. Separei em dois
ciclos pra não entregar um PR gigante de uma vez só:

| Ciclo | Funcionalidade | Status |
|---|---|---|
| **2a** | Gestão de Cardápio (CRUD de produtos) | **este documento** |
| 2b | Fluxo de status do pedido + conta detalhada + tela de cozinha | depois, com seu próprio design |

---

## 2. Problema que encontrei no código existente

O nome do produto que aparece num pedido hoje vem **ao vivo** da tabela
`produto` (`item.produto.nome`, lido na hora de montar a resposta). Isso
nunca deu problema na Fase 1 porque o cardápio era fixo — mas assim que ele
virar editável, renomear um hambúrguer **reescreveria o nome em pedidos
antigos**. É o mesmo tipo de bug que já corrigi pro preço (`preco_unitario`
já é uma foto do momento do pedido; o nome não era).

Vou corrigir isso como parte da Fase 2a, não deixar pra depois:
`ItemPedido` ganha uma coluna `produto_nome`, gravada na criação do pedido
igual já acontece com `preco_unitario`.

---

## 3. Modelo de dados

### `ItemPedido` — campo novo

| Campo | Tipo | Regra |
|---|---|---|
| `produto_nome` | str(80) | snapshot do `nome` do produto no momento do pedido; gravado em `_montar_itens`, nunca mais muda |

O restante do modelo (`Produto`, `Pedido`, demais campos de `ItemPedido`) não
muda. A FK `ItemPedido.produto_id → Produto.id` continua existindo, mas a
exibição (nome, preço) passa a vir inteiramente do snapshot — não preciso
mais navegar o relacionamento `item.produto` pra montar a resposta.

### Regra nova: exclusão de produto

Como a FK `produto_id` não tem `ON DELETE SET NULL`, excluir um produto que
já apareceu em algum pedido quebraria a integridade (ou o pedido antigo fica
com uma referência morta). Decidi: **bloquear a exclusão** se existir pelo
menos um `ItemPedido` com aquele `produto_id`, com uma mensagem de erro que
sugere marcar como indisponível em vez de excluir. É a mesma filosofia que
já uso pra outras regras de negócio (validação no `crud.py`, não no banco).

---

## 4. API — novos endpoints em `/api/produtos`

| Método | Rota | Descrição | Códigos |
|---|---|---|---|
| `POST` | `/api/produtos` | Cria um produto | 201, 400, 422 |
| `PUT` | `/api/produtos/{id}` | Substitui nome, descrição, preço, categoria, disponibilidade | 200, 400, 404, 422 |
| `DELETE` | `/api/produtos/{id}` | Exclui o produto | 204, 400, 404 |

(`GET /api/produtos` e `GET /api/produtos/{id}`, da Fase 1, continuam iguais.)

### Contrato de entrada (`POST` e `PUT`)

```json
{
  "nome": "X-Frango",
  "descricao": "Frango grelhado, queijo, alface e maionese",
  "preco": "21.50",
  "categoria": "Clássicos",
  "disponivel": true
}
```

### Regras de negócio (validadas no backend)

- `nome`: obrigatório, 1–80 caracteres, **único** — `POST` ou `PUT` com nome
  já usado por outro produto → `400` (`"Já existe um produto chamado
  '<nome>'."`). No `PUT`, o próprio produto não conta como conflito consigo
  mesmo.
- `preco`: obrigatório, **> 0** → senão `422` (Pydantic, `Field(gt=0)`).
- `categoria`: obrigatória, 1–40 caracteres.
- `disponivel`: opcional, default `true`.
- `DELETE`: bloqueado com `400` se o produto está referenciado em algum
  `ItemPedido` (`"Não é possível excluir — esse produto já aparece em
  pedidos. Marque como indisponível em vez de excluir."`).
- `PUT`/`DELETE` em produto inexistente → `404`.

---

## 5. Frontend — nova página `cardapio-admin.html`

Separei a gestão de cardápio da tela de pedidos (`index.html`) — são
públicos diferentes (quem tira o pedido não precisa ficar editando o
cardápio o tempo todo) e evita o `app.js` da Fase 1 virar um arquivo fazendo
cardápio-de-pedido + carrinho + pedidos + agora também CRUD de produto.

- **`cardapio-admin.html`** + **`admin.js`** (própria lógica, não mexe em
  `app.js`).
- Formulário: nome, descrição, preço, categoria, checkbox disponível.
  Botão "Salvar produto" (cria) ou "Salvar alterações" (edita) — mesmo
  padrão de alternância que `app.js` já usa pro formulário de pedido.
- Tabela com **todos** os produtos (inclusive indisponíveis, usando
  `?incluir_indisponiveis=true`), colunas: nome, categoria, preço,
  disponível (sim/não), e ações **Editar** / **Excluir**.
- Link de navegação simples no topo das duas páginas: `Pedidos | Cardápio`.
- Mesmo padrão de erro das outras páginas: faixa de aviso lendo o `detail`
  da API.
- Reaproveita `styles.css` (adiciono só as classes que faltarem, ex. para a
  tabela de produtos e o checkbox).

Decisão consciente: `admin.js` repete pequenos helpers que já existem em
`app.js` (`api()`, `aviso()`, `brl()` — umas 20 linhas no total) em vez de
criar um módulo JS compartilhado. Pro tamanho do projeto, a duplicação
pequena é mais simples de ler do que resolver carregamento de módulo entre
páginas estáticas sem build.

---

## 6. Tratamento de erros

Mesmo padrão da Fase 1: Pydantic cobre formato (`422`), `RegraNegocioError`
no `crud.py` cobre regra de negócio (`400`/`404` no router), sessão por
requisição, frontend trata toda resposta não-OK.

---

## 7. Testes (pytest)

Vou cobrir pelo menos:

- Criar produto válido → `201`, confere os campos na resposta.
- Criar com nome duplicado → `400`.
- Criar com preço ≤ 0 → `422`.
- Editar produto (nome, preço, disponibilidade) → `200`, confere mudança.
- Editar usando o nome de **outro** produto existente → `400`.
- Editar produto inexistente → `404`.
- Excluir produto sem pedidos associados → `204`, some do `GET /api/produtos`.
- Excluir produto **com** pedido associado → `400`, produto continua existindo.
- Excluir produto inexistente → `404`.
- Criar um pedido e confirmar que `item.produto_nome` grava o nome correto
  no momento da criação.
- Editar o nome do produto **depois** de criar um pedido com ele → o pedido
  antigo continua mostrando o nome original (`GET /api/pedidos/{id}`).

Lista exata (com o código de cada teste) vai no plano de implementação.

---

## 8. Fora de escopo nesse ciclo (fica pra 2b ou depois)

- Mudança de status do pedido, conta detalhada, tela de cozinha → Fase 2b.
- Restringir edição/exclusão de pedido conforme o status → Fase 2b (porque
  depende do campo de status existir de verdade).
- Upload de imagem do produto, categorias como tabela própria (hoje
  `categoria` continua sendo só um texto livre) — YAGNI pro escopo do
  trabalho.

---

## 9. Riscos e decisões em aberto

| Item | Decisão |
|---|---|
| Schema sem Alembic | `produto_nome` é coluna nova; `Base.metadata.create_all` não altera tabela existente. Preciso apagar `backend/app.db` antes de testar essa fase (mesma recomendação que já dou antes de gravar vídeo). |
| Nome de produto duplicado com acentuação/caixa diferente (`"X-Salada"` vs `"x-salada"`) | Não vou tratar — comparo exatamente como veio. Considero fora de escopo pro trabalho. |
| Categoria como texto livre | Mantenho assim (igual Fase 1); criar uma tabela de categorias é mais estrutura do que o escopo pede agora. |
