# Backlog para a Fase 2 (itens que adiei nas revisões da Fase 1)

Nenhum destes bloqueia a Fase 1. São melhorias que anotei para encaixar quando
a Fase 2 (CRUD de cardápio) mexer nas áreas relacionadas.

## Segurança / front-end

- `frontend/app.js`: trocar a interpolação em `innerHTML` por `textContent` /
  `createElement` ou um helper `esc()`. A superfície de XSS cresce na Fase 2,
  quando `nome`/`descricao` do produto passam a ser editáveis pelo usuário
  (hoje só `cliente_nome` e `observacao` chegam via input).

## Back-end — limpeza

- `backend/app/routers/pedidos.py`: `raise HTTPException(...) from erro`
  (preserva a causa; silencia o aviso B904 do ruff).
- `backend/app/routers/produtos.py`: remover a anotação `-> list` "pelada".
- `backend/app/schemas.py`: um `field_validator` que dá `strip()` e revalida
  `cliente_nome` (hoje `"   "` passa no `min_length=1`).
- `backend/app/main.py`: mover os `import` dos routers para o escopo do
  módulo (manter só o `import app.seed` adiado, que é proposital e documentado).
- `backend/app/database.py`: tirar o `DB_DIR.mkdir(...)` do import e chamar
  dentro de uma função.
- Considerar um `TypeDecorator` de SQLAlchemy para as colunas de data, de
  modo que o atributo do ORM já venha tz-aware em memória (hoje só a
  serialização JSON força UTC).

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
