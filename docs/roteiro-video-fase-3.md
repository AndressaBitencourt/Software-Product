# Roteiro do vídeo — Apresentação da Fase 3

Roteiro para gravação de tela, ~5min a 5min30. Fala natural, sem pressa — os
tempos abaixo são só uma referência para não passar do limite. Essa é a
última fase do projeto.

**A ideia central:** fazer um pedido **anônimo**, pelo celular/navegador sem
estar logado — como um cliente de verdade faria — e mostrar ele aparecendo
na hora no painel do atendente depois de logar. Isso prova duas coisas ao
mesmo tempo: que o checkout público é real (mesmo banco de dados) e que a
proteção por papel (atendente / admin) funciona de verdade, não é só duas
telas diferentes.

## Antes de gravar (checklist)

- [ ] Fechar abas e programas que não vão aparecer no vídeo
- [ ] Deixar só 2 janelas prontas: **navegador** (em branco, sem abrir ainda)
      e **VSCode** com o projeto aberto
- [ ] Apagar `backend/app.db` para o banco começar limpo (Finder ou
      `rm backend/app.db`) — assim o cardápio aparece do seed e a lista de
      pedidos começa vazia
- [ ] Ter o terminal do VSCode aberto na pasta do projeto
- [ ] Ter as duas credenciais de demonstração à mão: admin
      (`admin@hamburgueria.com` / `admin123`) e atendente
      (`atendente@hamburgueria.com` / `atendente123`) — estão no README
- [ ] Vai usar o **seu próprio nome** como cliente na hora de finalizar o
      pedido anônimo — é por ele que você vai identificar o pedido no painel
      depois
- [ ] Testar o `EXECUTE-AQUI` uma vez antes de gravar, pra garantir que sobe
      sem erro

---

## 0:00 – 0:25 — Abertura

**Tela:** VSCode aberto, mostrando a raiz do projeto.

**Fala:**
> Oi, de novo! Essa é a apresentação da **Fase 3**, a última do meu sistema
> de pedidos da hamburgueria. Nela eu adicionei login com dois perfis —
> atendente e admin — protegendo as rotas sensíveis, uma página de
> relatórios com gráficos, e depois da entrega eu revi uma decisão: agora o
> cardápio e o carrinho são **públicos**, sem precisar de login, porque faz
> mais sentido o próprio cliente montar o pedido pelo celular.

---

## 0:25 – 0:45 — Subindo o app

**Tela:** terminal do VSCode.

**Ação:** digitar e rodar
```
./EXECUTE-AQUI.sh
```
(ou `EXECUTE-AQUI.bat` se estiver gravando no Windows)

---

## 0:45 – 1:45 — Fluxo público: o cliente faz o próprio pedido

**Tela:** navegador em `http://localhost:8000`.

**Fala:**
> Essa é a loja — ninguém precisa logar pra ver o cardápio nem pra pedir.

**Ação:** clicar em "Adicionar" em 1 ou 2 produtos, apontar o toast que
aparece confirmando e o contador que sobe no ícone do carrinho, no canto
superior direito.

**Fala:**
> Cada "Adicionar" mostra uma confirmação rápida e atualiza o contador do
> carrinho, que fica salvo no navegador mesmo trocando de página.

**Ação:** clicar no ícone do carrinho, abrir `/carrinho.html`, ajustar a
quantidade de um item, preencher **o seu próprio nome** no campo de cliente,
clicar em "Finalizar Pedido".

**Fala:**
> No carrinho dá pra ajustar quantidade e remover item. Preencho meu nome e
> finalizo — isso cria o pedido de verdade no banco, sem eu ter logado em
> nada.

**Ação:** apontar a tela de confirmação (número do pedido + total).

---

## 1:45 – 2:00 — Tentando acessar a área do funcionário

**Tela:** abrir o menu ☰ → "Área do Funcionário", ou digitar
`/painel-pedidos.html` direto na URL.

**Fala:**
> Se eu tentar abrir o painel de pedidos sem estar logado, a API bloqueia e
> a tela me manda pro login.

---

## 2:00 – 2:50 — Login como atendente

**Tela:** `/login.html`, logar com `atendente@hamburgueria.com` /
`atendente123`.

**Fala:**
> Agora logo como atendente.

**Ação:** apontar o pedido que acabou de ser criado (com o seu nome)
aparecendo na lista do painel. Clicar em "Ver" pra mostrar o detalhe, depois
apontar o menu ☰ mostrando que só tem "Painel de Pedidos" — sem "Gerenciar
Cardápio" nem "Relatórios".

**Fala:**
> E aqui está o pedido que acabei de fazer como cliente, já na lista — mesmo
> banco de dados dos dois lados. O atendente só vê e acompanha pedidos; não
> tem acesso à gestão de cardápio nem aos relatórios, que são só do admin.

---

## 2:50 – 3:10 — Trocando para o admin

**Tela:** "Sair", logar de novo com `admin@hamburgueria.com` / `admin123`.

**Fala:**
> Saio e entro como admin, que tem o mesmo painel de pedidos **mais**
> Gerenciar Cardápio e Relatórios no menu.

---

## 3:10 – 4:10 — Relatórios

**Tela:** abrir "Relatórios".

**Fala:**
> Aqui tem um resumo do período — total de pedidos, faturamento e ticket
> médio — e dois gráficos: faturamento por dia e os produtos mais vendidos.

**Ação:** mudar o filtro de data, mostrar os cards de resumo atualizando.

**Ação:** apontar o gráfico de faturamento (barras com gradiente no card
escuro) e o de produtos mais vendidos (cada barra com uma cor).

**Ação:** usar a busca por nome do cliente na parte de baixo, buscando pelo
seu próprio nome — mostrar o pedido do carrinho aparecendo também aqui.

**Fala:**
> E dá pra buscar pedidos por nome de cliente, com o mesmo filtro de data —
> reaproveita o mesmo endpoint de listar pedidos.

---

## 4:10 – 4:45 — Código

**Tela:** VSCode, abrir `backend/app/auth.py`.

**Fala:**
> No back-end, a proteção é por duas dependências do FastAPI: `usuario_logado`,
> que vale pra atendente e admin, e `usuario_admin`, que builda em cima dela e
> bloqueia quem não é admin. A senha nunca fica em texto puro — é hash com
> bcrypt — e a sessão fica numa tabela no banco, não num token JWT, então dar
> logout de verdade é só apagar a linha.

**Ação:** abrir `backend/app/routers/produtos.py` e `pedidos.py`, apontar
rapidamente que `GET /produtos` e `POST /pedidos` não têm mais a dependência
de login, enquanto `GET/PUT/DELETE /pedidos` continuam exigindo.

---

## 4:45 – 5:15 — Testes e fechamento

**Tela:** terminal.

**Ação:** rodar
```
./EXECUTE-AQUI.sh test
```

**Fala:**
> E pra fechar, os testes automatizados — agora são 85, cobrindo desde o
> CRUD da Fase 1 até login, permissão por papel e os relatórios dessa fase.

**Tela:** parado no resultado `85 passed`.

**Fala:**
> Essa foi a Fase 3, e com ela o projeto está completo: CRUD de pedidos,
> gestão de cardápio, e agora login com perfis e relatórios. Obrigada!

---

## Dicas de gravação

- Fale um pouco mais devagar do que o normal — no vídeo sempre parece mais
  rápido do que parece na hora.
- Se travar numa parte, pausa a gravação, respira e regrava só aquele trecho
  (dá pra cortar depois).
- Não precisa decorar a fala palavra por palavra — usa esse roteiro como guia
  e fala com as suas palavras.
- Se o vídeo ficar longo demais, o trecho de código (4:10–4:45) é o mais
  fácil de cortar sem perder a demonstração funcional.
