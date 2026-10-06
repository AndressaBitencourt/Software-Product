# Backlog para a Fase 2 (itens que adiei nas revisões da Fase 1)

Nenhum destes bloqueia a Fase 1. São melhorias que anotei para encaixar quando
a Fase 2 (CRUD de cardápio) mexer nas áreas relacionadas.

## Back-end — limpeza

- `backend/app/routers/pedidos.py`: `raise HTTPException(...) from erro`
  (preserva a causa; silencia o aviso B904 do ruff). Já apliquei isso em
  `routers/produtos.py` na revisão final da Fase 2a — falta só esse arquivo.
- `backend/app/schemas.py`: um `field_validator` que dá `strip()` e revalida
  `cliente_nome` (hoje `"   "` passa no `min_length=1`). Já fiz o mesmo pra
  `nome`/`categoria` de `ProdutoIn` na Fase 2a — só falta esse campo.
- `backend/app/main.py`: mover os `import` dos routers para o escopo do
  módulo (manter só o `import app.seed` adiado, que é proposital e documentado).
- `backend/app/database.py`: tirar o `DB_DIR.mkdir(...)` do import e chamar
  dentro de uma função.
- `backend/app/crud.py`: `excluir_produto` ficou no fim do arquivo, longe de
  `criar_produto`/`atualizar_produto` (cada tarefa da Fase 2a acrescentou no
  fim do arquivo). Mover pra perto das outras funções de produto.
- Considerar um `TypeDecorator` de SQLAlchemy para as colunas de data, de
  modo que o atributo do ORM já venha tz-aware em memória (hoje só a
  serialização JSON força UTC).

## Para pensar no design da Fase 2b

- A checagem de disponibilidade em `crud._montar_itens` responde duas
  perguntas diferentes com uma regra só: "esse produto pode aparecer num
  pedido novo" vs. "esse produto pode continuar num pedido que já existia".
  Na Fase 2a resolvi isso com o parâmetro `produtos_ja_aceitos` (um item que
  já estava no pedido não é barrado se o produto virou indisponível depois).
  O fluxo de status da Fase 2b vai mexer mais em pedidos já existentes —
  vale revisar se essa regra ainda faz sentido quando um pedido já está "Em
  preparo", por exemplo.

## Testes

- Afirmar o corpo `detail` (não só o `status_code`) nos caminhos de erro
  de PUT/DELETE e de alguns de produtos.
- `test_listar_pedidos`: afirmar `quantidade_itens == 3` num pedido com 2
  linhas e 3 unidades (fixa o contrato para os relatórios da Fase 3).
- `test_get_produtos_retorna_seed`: afirmar a ordenação `categoria, nome`.
- A comparação de timestamps em `test_editar_pedido_recalcula_total` é
  lexicográfica de string — trocar por `datetime.fromisoformat`.

## Docker

- `.dockerignore`: prefixo `**/` também em `.DS_Store`.
- Build multi-stage para não levar `pytest`/`httpx` para a imagem final.

## Resolvido nas melhorias visuais da Fase 2a

- ~~`frontend/app.js` e `frontend/admin.js`: escapar interpolação em
  `innerHTML`~~ — feito. Adicionei um helper `esc()` (duplicado nos dois
  arquivos) e apliquei em todo ponto que interpola texto livre
  (nome/categoria/descrição de produto, nome do cliente, observação,
  nome do produto no detalhe do pedido). A revisão final achou que dava
  pra quebrar atributo (`alt=`/`src=`) com aspas no nome do produto —
  por isso resolvi na hora em vez de adiar de novo.

## Fotos do cardápio inicial

- Trocadas as 8 ilustrações SVG do seed por fotos reais (Pexels License —
  uso comercial livre, sem exigência de atribuição). Créditos mantidos em
  `frontend/images/seed/CREDITS.md` por transparência, não por obrigação.
  `placeholder.svg` continua sendo ilustração própria (fallback para
  produto sem foto).

## Itens menores que adiei de novo (não bloqueiam nada)

- `frontend/images/seed/placeholder.svg` não tem quebra de linha no fim
  do arquivo — cosmético, sem config de lint no projeto que reclame. (Os
  outros 8 SVGs do seed inicial foram substituídos por fotos reais — ver
  "Fotos do cardápio inicial" abaixo.)
- 3 dos 6 testes de upload com erro (formato inválido, produto
  inexistente, tamanho excedido) checam só o `status_code`, não que zero
  arquivos foram gravados — o comportamento está certo (confirmei), só
  falta a asserção que provaria isso formalmente.
