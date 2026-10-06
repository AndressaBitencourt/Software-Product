# Software-Product — Sistema de Pedidos de Hamburgueria

## Meu documento de design — melhorias visuais da Fase 2a

- **Data:** 2026-10-13
- **Branch:** continuo na `fase-2a` (PR #8 ainda aberto) — é polimento de telas que acabei
  de construir, não faz sentido abrir outro PR só pra isso.

Depois que terminei o CRUD de cardápio, decidi dar uma repaginada nas duas
telas antes de mergear: visual mais moderno, campo de categoria com
sugestões, e foto nos produtos. Escrevo esse documento antes de codar.

---

## 1. Visão geral

Três melhorias, todas de UI (não mexem na API que já existe, exceto a parte
de imagem que precisa de um endpoint novo):

1. **Visual "Chapa Quente"** — nova paleta de cor, tipografia, e um menu
   hambúrguer (☰) no lugar dos links soltos do header.
2. **Categoria com sugestões** — o campo de categoria no formulário de
   produto vira um campo com `<datalist>`: mostra as categorias que já
   existem, mas ainda deixa digitar uma nova.
3. **Foto nos produtos** — upload de uma imagem por produto, mostrada no
   cardápio e na tela de gestão. Os 8 itens do seed já vêm com ilustração
   (desenhei eu, sem usar foto de terceiro — risco de direito autoral).

---

## 2. Visual "Chapa Quente"

Escolhi comparando 3 direções visuais lado a lado (mockups numa Artifact) —
essa foi a escolhida.

### Paleta (variáveis CSS em `styles.css`)

```css
--bg: #FAF6EF;        /* fundo da página */
--surface: #FFFFFF;   /* cards, menus, tabela */
--ink: #2B2420;        /* texto principal */
--muted: #8C7F6E;      /* texto secundário */
--line: #EADFCB;       /* bordas sutis */
--header: #7A1F1F;     /* header, botão principal */
--header-ink: #FBEADB; /* texto sobre o header */
--accent: #E8A33D;     /* botão do menu hambúrguer, destaques */
--accent-ink: #3A2200; /* texto sobre o accent */
```

### Tipografia

**Fraunces** (serifada, pros títulos: `h1`, `h2`, `h3`) + **Work Sans**
(pro resto). Carrego via `<link>` do Google Fonts no `<head>` das duas
páginas.

### Menu hambúrguer

Troco os links soltos do header por um botão `☰` que abre um dropdown:

```html
<header>
  <h1>🍔 Hamburgueria</h1>
  <button class="hamb-btn" id="btn-menu" aria-label="Abrir menu" aria-expanded="false">☰</button>
  <nav class="hamb-menu" id="menu-nav" hidden>
    <a href="/" class="active">Pedidos</a>
    <a href="/cardapio-admin.html">Cardápio</a>
  </nav>
</header>
```

Um JS pequeno (duplicado entre `app.js` e `admin.js`, igual já faço com
`api()`/`aviso()`/`brl()`) abre/fecha ao clicar no botão e fecha se eu
clicar fora. Em cada página, o link da própria página já vem com
`class="active"` escrito direto no HTML — não precisa de JS pra isso.

### Resto da repaginada

Cards, tabela e campos de formulário ganham cantos mais arredondados
(`border-radius: 10-11px`), bordas na cor `--line`, sombra leve. Botões
usam a nova paleta. Aplico em `styles.css`, que já é compartilhado pelas
duas páginas — a maior parte da mudança é um arquivo só.

---

## 3. Categoria com sugestões

```html
<label>Categoria
  <input type="text" id="categoria" maxlength="40" required list="categorias-lista" />
  <datalist id="categorias-lista"></datalist>
</label>
```

Em `admin.js`, toda vez que a lista de produtos recarrega, preencho o
`<datalist>` com as categorias distintas que já existem (`Set` +
`sort()`). Continua sendo um campo de texto — o navegador mostra as opções
como sugestão, mas uma categoria nova ainda pode ser digitada.

---

## 4. Foto nos produtos

### Banco

`Produto` ganha a coluna `imagem_url: str | None` (caminho relativo tipo
`/uploads/produtos/3-a1b2c3d4.jpg` ou `/images/seed/x-salada.svg`).

### Armazenamento

- Fotos **enviadas pelo usuário** vão pra `backend/uploads/produtos/`
  (pasta nova, **não entra no git** — adiciono no `.gitignore`). Nome do
  arquivo: `{produto_id}-{hash curto}.{extensão}`, pra nunca colidir.
- As **ilustrações do seed** (desenhadas por mim) ficam em
  `frontend/images/seed/*.svg` — essas sim entram no git, fazem parte do
  app.
- As duas pastas são servidas como arquivo estático: a de upload num mount
  novo (`/uploads`), a do seed já cai dentro do mount que já existe pro
  `frontend/` inteiro.

### Endpoint novo

| Método | Rota | Descrição | Códigos |
|---|---|---|---|
| `POST` | `/api/produtos/{id}/imagem` | Envia/substitui a foto do produto (`multipart/form-data`, campo `arquivo`) | 200, 400, 404 |

Fica separado do `POST`/`PUT` de produto (que continuam JSON) porque
upload de arquivo é outro formato de requisição.

### Regras de negócio

- Só aceito `.jpg`, `.jpeg`, `.png`, `.webp` — outro formato → `400`.
- Limite de **5 MB** — maior que isso → `400`.
- Produto inexistente → `404`.
- Ao enviar uma foto nova, **apago o arquivo anterior** do disco (não
  acumula lixo).
- Ao **excluir um produto**, apago o arquivo de imagem dele também (se
  tiver).
- Editar um produto (`PUT`) nunca mexe na foto — só muda quando eu chamo o
  endpoint de imagem.

### As 8 ilustrações

Desenho eu, em SVG, no estilo "Chapa Quente" (cores do hambúrguer, batata,
bebida combinando com a paleta nova): X-Salada, X-Bacon, X-Tudo,
X-Vegetariano, Batata Frita, Onion Rings, Refrigerante Lata, Suco Natural.
Mais um **placeholder genérico** pra produto criado sem foto.

### Front-end

- **Cardápio (`index.html`/`app.js`)**: cada card ganha uma imagem no topo
  (a do produto, ou o placeholder se não tiver).
- **Gestão (`cardapio-admin.html`/`admin.js`)**: campo de arquivo no
  formulário com prévia (local, antes de enviar) + miniatura na tabela.
  Fluxo pra salvar: primeiro crio/atualizo o produto (JSON, como já
  funciona), e **se** escolhi um arquivo, mando ele em seguida pro
  endpoint de imagem. Duas chamadas HTTP, uma ação só pro usuário.

---

## 5. Testes

- Testes já existentes que checam as chaves da resposta de `/api/produtos`
  (`test_get_produtos_retorna_seed`) precisam incluir `imagem_url` no
  conjunto esperado — vou atualizar, não é regressão, é o contrato mudando
  de propósito.
- Upload válido, formato inválido, tamanho maior que 5 MB, produto
  inexistente, substituir imagem anterior (apaga a antiga), excluir
  produto remove o arquivo.
- Pra não sujar a pasta `backend/uploads/` de verdade durante os testes,
  uso uma fixture com `tmp_path` do pytest + `monkeypatch` apontando o
  módulo de upload pra uma pasta temporária.

---

## 6. Fora de escopo

- Múltiplas fotos por produto (só uma).
- Recorte/redimensionamento de imagem no servidor (confio no que o
  usuário manda, só limito tamanho de arquivo).
- Imagem em pedido/item de pedido — só no cardápio.

---

## 7. Riscos e decisões em aberto

| Item | Decisão |
|---|---|
| Sem Alembic, de novo | Coluna nova em `produto` — preciso apagar `backend/app.db` antes de testar, mesma situação de toda mudança de schema nesse projeto. |
| `python-multipart` | O FastAPI precisa desse pacote pra ler upload de arquivo — entra no `requirements.txt`. |
| Pasta `backend/uploads/` em produção/Docker | Fica fora do volume `db-data` do `docker-compose.yml` por enquanto — então num container novo as fotos enviadas por upload se perdem ao recriar o container (as ilustrações do seed não, essas estão no código). Documento isso, não resolvo agora — não acho que vale a complexidade extra pro escopo do trabalho. |
