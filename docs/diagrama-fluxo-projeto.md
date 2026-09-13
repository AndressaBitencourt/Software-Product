# Diagrama de fluxo do projeto

Visão geral de como as peças da Fase 1 se conectam: quem chama quem, do
clique na tela até a gravação no banco.

```mermaid
flowchart TD
    subgraph Navegador["Navegador"]
        Pessoa(["Pessoa fazendo o pedido"])
        Frontend["Frontend<br/>HTML + CSS + JS"]
    end

    subgraph Servidor["Back-end (FastAPI)"]
        Routers["Routers<br/>endpoints /api"]
        Regras["Regras de negócio<br/>crud.py"]
        ORM["SQLAlchemy<br/>models e schemas"]
    end

    DB[("SQLite<br/>backend/app.db")]

    Pessoa --> Frontend
    Frontend <-->|requisição HTTP / resposta JSON| Routers
    Routers --> Regras --> ORM --> DB

    classDef cliente fill:#fde68a,stroke:#b45309,color:#78350f
    classDef servidor fill:#bfdbfe,stroke:#1d4ed8,color:#1e3a8a
    classDef dados fill:#bbf7d0,stroke:#15803d,color:#14532d

    class Pessoa,Frontend cliente
    class Routers,Regras,ORM servidor
    class DB dados
```

## Explicação

- A pessoa interage com o **frontend** no navegador.
- O frontend chama a **API** (`routers/`), que passa pelas **regras de
  negócio** (`crud.py`) antes de ler ou gravar no banco através do
  **SQLAlchemy** (`models.py` / `schemas.py`).
- A resposta volta em JSON e o frontend atualiza a tela, sem recarregar a
  página.
