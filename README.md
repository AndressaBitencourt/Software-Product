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
