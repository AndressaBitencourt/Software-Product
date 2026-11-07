# Software-Product — Sistema de Pedidos da Hamburgueria

Este é o meu trabalho de faculdade, entregue em 3 fases. Na **Fase 1** eu fiz o
CRUD completo de pedidos, com front-end, back-end e banco de dados. Na **Fase
2** acrescentei a gestão de cardápio — criar, editar e excluir produtos, com
fotos, categorias e promoções, numa página própria. Na **Fase 3** adicionei
login com perfis (atendente / admin), protegendo as rotas sensíveis,
e uma página de relatórios com resumo de vendas, gráficos e busca de pedidos.

Depois da entrega da Fase 3, revi a decisão de "cliente não loga": agora o
cardápio e o carrinho são públicos (o cliente monta e finaliza o próprio
pedido pelo celular, sem precisar de atendente), e quem loga (atendente /
admin) usa o **Painel de Pedidos** pra acompanhar o que chega. Ver
`docs/design-fase-3.md`, seção 10, pro histórico dessa mudança.

## Tecnologias que usei

- Back-end: Python 3.12 + FastAPI
- Banco: SQLite (arquivo `app.db`) via SQLAlchemy
- Front-end: HTML + CSS + JavaScript puro (sem build)
- Testes: pytest
- Empacotamento: Docker + docker-compose

## Como rodar

> **Atualizando de uma fase anterior?** Apague `backend/app.db` (ou rode
> `docker compose down -v`) antes de subir — a Fase 2a adicionou colunas
> novas (`item_pedido.produto_nome`, `produto.imagem_url`, `produto.em_promocao`,
> `produto.preco_promocional`) e o projeto não tem migração de schema (sem
> Alembic), então um banco antigo quebra com
> `no such column`.

> **Login padrão (Fase 3):** e-mail `admin@hamburgueria.com`, senha
> `admin123` (perfil admin) — criado automaticamente na primeira execução.
> Também existe um login de demonstração com perfil atendente: e-mail
> `atendente@hamburgueria.com`, senha `atendente123`. São só credenciais de
> demonstração para a entrega da faculdade. **Esse login só é necessário
> pra acompanhar os pedidos (`/painel-pedidos.html`)** — o cardápio (`/`) e
> o carrinho (`/carrinho.html`) são públicos, qualquer cliente usa sem
> entrar com conta.

### Opção mais fácil — script pronto

Fiz um script que acha o Python (instala sozinho se faltar), cria o ambiente
virtual, instala as dependências e sobe o app. Não precisa de Docker.

- macOS / Linux: `./EXECUTE-AQUI.sh`
- Windows: dê dois cliques em `EXECUTE-AQUI.bat` (ou rode no terminal)

Para rodar os testes em vez do servidor: `./EXECUTE-AQUI.sh test` (ou `EXECUTE-AQUI.bat test`).

### Opção A — Docker (funciona igual em macOS e Windows)

Pré-requisito: Docker Desktop instalado e aberto.

```
docker compose up --build
```

Depois é só acessar:
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
primeira execução e já vem populado com o cardápio inicial.

## Rodar os testes

```
cd backend
pip install -r requirements.txt
pytest -v
```

## Estrutura

- `backend/app/` — API FastAPI (models, schemas, crud, serializers, routers)
- `backend/tests/` — meus testes automatizados
- `frontend/` — páginas servidas pelo próprio back-end: cardápio público (`index.html`), carrinho (`carrinho.html`), painel de pedidos (`painel-pedidos.html`, exige login), gestão de cardápio (`cardapio-admin.html`), login (`login.html`) e relatórios (`relatorios.html`)
- `docs/` — o design e o plano de implementação que escrevi antes de codar

## Roadmap

| Fase | O que entra | Status |
| --- | --- | --- |
| 1 | CRUD de pedidos | ✅ Feito |
| 2 | Gestão de cardápio (CRUD de produtos, fotos, promoções) | ✅ Feito (escopo reduzido — ver nota abaixo) |
| 3 | Login e perfis (atendente / admin) + relatórios e dashboard | ✅ Feito |

> A Fase 2 originalmente incluía também o fluxo de status do pedido
> (Recebido → Preparo → Pronto → Entregue/Cancelado), conta detalhada e tela
> de cozinha. Decidi cortar essa parte e fechar a fase só com a gestão de
> cardápio — ver `docs/design-fase-1.md` para o histórico da decisão.
