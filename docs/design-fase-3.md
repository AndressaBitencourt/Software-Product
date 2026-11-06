# Software-Product — Sistema de Pedidos de Hamburgueria

## Meu documento de design — Fase 3 (Login e Perfis + Relatórios)

- **Data:** 2026-11-06
- **Repositório:** `AndressaBitencourt/Software-Product` (público), branch a
  partir de `main` (já com a Fase 1 e a Fase 2 mergeadas)
- **Entrega:** última fase do projeto. Diferente da Fase 2, não separei essa
  em ciclos — login e relatórios ficam num plano só, porque relatórios
  dependem de login existir (só admin acessa).

Escrevi este documento antes de codar, pra fechar o escopo da Fase 3 e
registrar as decisões técnicas.

---

## 1. Visão geral

A Fase 2 foi fechada com escopo reduzido — só a gestão de cardápio, sem o
fluxo de status do pedido (ver histórico em `design-fase-1.md`). Isso afeta
essa fase: os relatórios de faturamento consideram **todos** os pedidos, sem
filtrar por status, porque hoje não existe forma de cancelar um pedido.

Essa fase junta as duas funcionalidades que sobraram do roadmap original:

| Parte | Funcionalidade |
| --- | --- |
| Autenticação | Login com papéis **atendente** e **admin**, rotas protegidas |
| Relatórios | Faturamento por dia, itens mais vendidos, total de pedidos, busca, filtros, gráficos |

**Decisão de escopo — "cliente" não loga.** O app hoje é uma ferramenta de
balcão: quem usa é o atendente, que digita o nome do cliente ao criar o
pedido — não é o cliente final pedindo pelo próprio celular. Fazer "cliente"
ser um papel que loga de verdade exigiria cadastro, confirmação de conta e
histórico de pedidos por usuário — um projeto bem maior, que muda a forma
como pedidos são criados hoje. Por isso só **atendente** e **admin** logam:

- **Atendente** — acessa a tela de Pedidos (ver cardápio, criar/editar/
  excluir pedido).
- **Admin** — tudo isso **+** Gerenciar Cardápio **+** Relatórios.

---

## 2. Modelo de dados

### Tabela `usuario`

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | int | PK |
| `nome` | str(80) | |
| `email` | str(120) | único, usado pra login |
| `senha_hash` | str(255) | hash bcrypt, nunca a senha em texto puro |
| `papel` | str(20) | `"atendente"` ou `"admin"` |
| `criado_em` | datetime (UTC) | |

### Tabela `sessao`

| Campo | Tipo | Regra |
| --- | --- | --- |
| `token` | str(64) | PK, UUID4 hex gerado no login |
| `usuario_id` | int | FK → `usuario.id`, `ondelete="CASCADE"` |
| `criado_em` | datetime (UTC) | |
| `expira_em` | datetime (UTC) | `criado_em` + 8h (duração de um turno) |

Sessão em tabela (não JWT): dá pra fazer logout de verdade apagando a linha,
não precisa de biblioteca de assinatura de token, e é mais simples de testar
— cada rota protegida só busca o token do cookie na tabela.

---

## 3. Autenticação

### Hash de senha

Biblioteca `bcrypt` (nova dependência, adiciono no `requirements.txt`).
`bcrypt.hashpw` no cadastro/seed, `bcrypt.checkpw` no login. Sem guardar
senha em texto puro em nenhum lugar, nem no seed (a senha do admin padrão só
aparece em texto puro no README, documentada como credencial de demo).

### Cookie de sessão

- Nome: `sessao_token`.
- `HttpOnly` — JavaScript não consegue ler, protege contra roubo via XSS.
- `SameSite=Lax` — o navegador não manda o cookie em requisições
  disparadas por outro site, cobrindo a maior parte do risco de CSRF sem
  precisar de um token extra.
- **Sem** a flag `Secure` — o projeto roda em HTTP local (`localhost:8000`,
  sem TLS). Isso é uma limitação conhecida: numa implantação de produção de
  verdade, com HTTPS, essa flag devia ser ligada.

### Dependências de rota (FastAPI `Depends`)

Novo módulo `backend/app/auth.py`:

```python
def usuario_logado(
    sessao_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """Qualquer papel. 401 se não houver sessão válida."""

def usuario_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    """Só admin. 403 se o papel não for admin."""
```

- `usuario_logado`: busca a sessão pelo token do cookie, confere que não
  expirou, carrega o usuário. Levanta `401` se não houver cookie, a sessão
  não existir ou tiver expirado.
- `usuario_admin`: reusa `usuario_logado` e levanta `403` se o papel não for
  `"admin"`.

### Rotas protegidas

| Rota | Proteção |
| --- | --- |
| `POST /api/login` | pública |
| `POST /api/logout` | precisa estar logado (qualquer papel) |
| `GET /api/me` | precisa estar logado (qualquer papel) — devolve usuário + papel, usado pelo front-end pra checar sessão |
| `GET /api/produtos`, `GET/POST/PUT/DELETE /api/pedidos` | `usuario_logado` (atendente ou admin) |
| `POST/PUT/DELETE /api/produtos`, `POST /api/produtos/{id}/imagem` | `usuario_admin` |
| `GET /api/relatorios/*` | `usuario_admin` |
| `GET /api/health` | pública (health check) |

---

## 4. Frontend

### Nova página `login.html`

Formulário simples — email + senha, botão "Entrar" — no mesmo visual
("Chapa Quente") do resto do app. Mostra mensagem de erro se a credencial
estiver errada (`401` da API).

### Proteção client-side

Como o front-end é HTML estático (sem servidor de template), a proteção de
verdade está na API — mas pra não mostrar a tela vazia/quebrada até a
chamada falhar, cada página protegida chama `GET /api/me` assim que carrega:

- `401` (sem sessão) → redireciona pra `/login.html`.
- Sessão válida mas papel sem permissão pra essa página (ex: atendente
  abrindo `/cardapio-admin.html` ou `/relatorios.html`) → redireciona de
  volta pra `/` com um aviso.
- Login certo → redireciona pra `/` (Pedidos).

Essa checagem entra no topo de `app.js`, `admin.js` e no novo
`relatorios.js` — seguindo o padrão já usado no projeto de duplicar
pequenos helpers em cada arquivo (não tem build step pra compartilhar
módulo).

### Menu (header)

Mostra o nome de quem está logado + botão "Sair". Os links mudam por papel:

- Atendente vê só "Pedidos".
- Admin vê "Pedidos", "Gerenciar Cardápio" e "Relatórios".

"Sair" chama `POST /api/logout` (apaga a sessão no banco) e redireciona pro
login.

---

## 5. Relatórios

### Nova página `relatorios.html` (só admin)

- 3 cards de resumo: total de pedidos, faturamento total, ticket médio —
  dentro de um filtro de período (padrão: últimos 30 dias).
- Gráfico de barras: faturamento por dia.
- Gráfico de barras horizontal: top 10 produtos mais vendidos (por
  quantidade).
- Tabela de pedidos com busca por nome do cliente + filtro de data.

### Endpoints novos (`backend/app/routers/relatorios.py`, todos `usuario_admin`)

- `GET /api/relatorios/resumo?data_inicio=&data_fim=` →
  `{total_pedidos, faturamento_total, ticket_medio}` — `ticket_medio` é
  `faturamento_total / total_pedidos` (zero se `total_pedidos` for zero, pra
  não dividir por zero)
- `GET /api/relatorios/faturamento-diario?data_inicio=&data_fim=` →
  `[{data, total}]`
- `GET /api/relatorios/produtos-mais-vendidos?data_inicio=&data_fim=&limite=10`
  → `[{produto_nome, quantidade_total}]`

`data_inicio`/`data_fim` são opcionais nos três endpoints de relatório — se
não vierem, o padrão é **últimos 30 dias** (calculado no servidor a partir
de `utcnow()`), igual ao período padrão mostrado nos cards de resumo.
`limite` em produtos-mais-vendidos tem padrão `10`.

A busca de pedidos reaproveita o `GET /api/pedidos` já existente — adiciono
parâmetros opcionais `cliente_nome`, `data_inicio`, `data_fim` (esses dois
sem padrão de 30 dias — se vazios, lista todos os pedidos, igual ao
comportamento atual), em vez de criar outro endpoint.

**Limitação conhecida:** sem o fluxo de status (Fase 2 reduzida), todo
pedido tem status `"recebido"` pra sempre — não existe pedido cancelado de
verdade no sistema. Os relatórios somam todos os pedidos sem filtrar por
status. Isso só precisa de ajuste se um dia o fluxo de status for
construído.

### Gráficos

Chart.js via CDN (`<script src="https://cdn.jsdelivr.net/npm/chart.js">`),
sem dependência Python nova. Dois `<canvas>` na página, alimentados pelos
dois primeiros endpoints acima.

---

## 6. Seed

`backend/app/seed.py` ganha `seed_usuarios(db)`, chamada em
`inicializar_banco()` junto com `seed_cardapio` — mesmo padrão. Cria um
usuário admin padrão se a tabela `usuario` estiver vazia:

- E-mail e senha fixos, documentados no `README.md` (seção "Como rodar"),
  marcados claramente como credencial de demonstração.

---

## 7. Testes

### Fixtures novos (`backend/tests/conftest.py`)

- `client` (já existe) — sem login. Usado pros casos de "sem sessão → 401"
  e pro próprio fluxo de login/logout.
- `client_atendente` — faz login de um usuário de teste com papel
  atendente, devolve o `TestClient` já com o cookie de sessão.
- `client_admin` — mesma ideia, com papel admin.

### Migração dos testes existentes

Os **60 testes atuais** chamam os endpoints de Pedidos e Produtos direto,
sem autenticação — vão quebrar assim que essas rotas passarem a exigir
login. A correção é mecânica: trocar `client` por `client_admin` (testes de
produto) ou `client_atendente` (testes de pedido) em `test_produtos.py` e
`test_pedidos.py`. `test_frontend.py` não muda (só testa HTML estático).

### Testes novos

- Login certo, login errado (senha e e-mail inválidos), logout.
- Acesso sem sessão → `401`.
- Acesso com papel errado (atendente em rota admin-only) → `403`.
- Os três endpoints de relatório, com pedidos conhecidos criados no teste.
- Busca/filtro de pedidos (`cliente_nome`, `data_inicio`, `data_fim`).

---

## 8. Dependências novas

- `bcrypt` — hash de senha (back-end, `requirements.txt`).
- Chart.js via CDN — gráficos (front-end, sem pacote Python).

Nenhuma outra dependência nova. Sessão em tabela não precisa de biblioteca
de JWT nem de assinatura de cookie.

---

## 9. Fora de escopo

- Fluxo de status do pedido / conta detalhada / tela de cozinha (cortado da
  Fase 2, ver `design-fase-1.md`).
- Cadastro/login de cliente.
- Recuperação de senha, convite de novo usuário por e-mail, ou qualquer tela
  de gestão de usuários — o único jeito de criar usuário nessa fase é o
  seed do admin padrão.
- Flag `Secure` no cookie de sessão (precisa de HTTPS, que o projeto não
  tem rodando localmente).
