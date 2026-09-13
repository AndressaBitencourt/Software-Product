# Roteiro do vídeo — Apresentação da Fase 1

Roteiro para gravação de tela, ~2min50 a 3min. Fala natural, sem pressa —
os tempos abaixo são só uma referência para não passar do limite.

**A ideia central:** o pedido criado ao vivo na demonstração **não é excluído**
— ele fica no banco de propósito, pra ser mostrado de verdade na parte de
código/banco lá na frente. Isso prova que os dados são reais, não é só a tela
"fingindo".

## Antes de gravar (checklist)

- [ ] Fechar abas e programas que não vão aparecer no vídeo
- [ ] Deixar só 2 janelas prontas: **navegador** (em branco, sem abrir ainda)
      e **VSCode** com o projeto aberto
- [ ] Apagar `backend/app.db` para o banco começar limpo (Finder ou
      `rm backend/app.db`) — assim o cardápio aparece do zero e a lista de
      pedidos começa vazia
- [ ] Ter o terminal do VSCode aberto na pasta do projeto
- [ ] Ter a extensão **SQLite Viewer** instalada no VSCode (pra abrir o
      `app.db` depois e mostrar o pedido de verdade)
- [ ] Vai usar o **seu próprio nome** como cliente na hora de criar o pedido —
      é ele que vai aparecer no banco depois
- [ ] Testar o `EXECUTE-AQUI` uma vez antes de gravar, pra garantir que sobe
      sem erro

---

## 0:00 – 0:15 — Abertura

**Tela:** VSCode aberto, mostrando a raiz do projeto (lista de pastas: `backend`,
`frontend`, `docs`, `README.md`).

**Fala:**
> Oi, meu nome é Andressa e esse é o meu trabalho de faculdade: um sistema de
> pedidos para uma hamburgueria. O projeto é entregue em 3 fases, e essa
> apresentação é da **Fase 1**, onde eu construí o CRUD completo de pedidos —
> com front-end, back-end e banco de dados.

---

## 0:15 – 0:35 — Tecnologias

**Tela:** abre `diagrama-fluxo-projeto.md` na prévia do Markdown (`Cmd+Shift+V`
no VSCode, ou a própria página do GitHub) e mostra o diagrama enquanto fala.

**Fala:**
> No back-end eu usei **Python com FastAPI**, o banco é **SQLite**, acessado
> com **SQLAlchemy**. O front-end é **HTML, CSS e JavaScript puro** — sem
> framework, sem processo de build. Esse diagrama aqui resume o fluxo: a
> pessoa interage com o front-end, que chama a API, passa pelas regras de
> negócio e cai no banco — e a resposta volta em JSON pra tela, sem
> recarregar a página. E eu escrevi **28 testes automatizados** com pytest,
> cobrindo os casos de sucesso e de erro.

---

## 0:35 – 0:50 — Subindo o app

**Tela:** terminal do VSCode. Roda o script.

**Fala:**
> Pra rodar, eu fiz um script que sobe tudo sozinho — sem precisar de Docker.

**Ação:** digitar e rodar
```
./EXECUTE-AQUI.sh
```
(ou `EXECUTE-AQUI.bat` se estiver gravando no Windows)

**Fala (enquanto sobe):**
> Ele confere se o Python está instalado, cria o ambiente virtual, instala as
> dependências e já abre o app no navegador.

---

## 0:50 – 1:40 — Demonstração funcional (o núcleo do vídeo)

**Tela:** navegador em `http://localhost:8000`.

**Fala:**
> Essa é a tela: o cardápio da hamburgueria, o formulário de novo pedido e a
> lista de pedidos.

**Ação:** apontar o cardápio.
> O cardápio já vem com 8 itens cadastrados no banco.

**Ação:** clicar em **"Adicionar"** em 2 itens diferentes (ex: X-Salada e
Batata Frita), ajustar a quantidade de um deles, preencher o **seu nome** no
campo de cliente.

**Fala:**
> Eu adiciono os itens no carrinho, ajusto a quantidade, e coloco o meu
> próprio nome aqui no cliente — vou usar esse pedido daqui a pouco pra
> mostrar que ele está de verdade salvo no banco de dados.

**Ação:** clicar em **"Fazer pedido"**.

**Fala:**
> Crio o pedido, e ele aparece na lista aqui embaixo, já com o total
> calculado pelo servidor.

**Ação:** clicar em **"Ver"** no pedido criado.

**Fala:**
> Dá pra ver o detalhe com os itens e o preço de cada um.

**Ação:** clicar em **"Editar"**, mudar um item ou a quantidade, salvar.

**Fala:**
> E editando o pedido, o total é recalculado na hora. Também dá pra excluir
> um pedido, mas esse eu vou deixar aqui de propósito — daqui a pouco eu
> mostro ele direto no banco de dados.

---

## 1:40 – 2:25 — Código e banco de dados

**Tela:** volta pro VSCode. Abre `backend/app/routers/pedidos.py`.

**Fala:**
> Por trás, o back-end é organizado em camadas: os **modelos** do banco, os
> **schemas** que validam o que entra e sai da API, a camada de **regras de
> negócio**, e os **routers**, que são os endpoints — esse aqui é o de
> pedidos, com criar, listar, editar e excluir.

**Ação (opcional):** rolar rapidamente até o endpoint de criar pedido,
apontar a validação de erro (ex: pedido sem item).

**Ação:** abrir `backend/app.db` no VSCode (com a extensão SQLite Viewer) e
clicar na tabela `pedido`.

**Fala:**
> E aqui está o banco de dados de verdade — o `app.db`, SQLite. Essa linha
> aqui é o pedido que eu acabei de criar pela tela, com o meu nome, o status
> e o total. Não é só uma tela bonita: está gravado mesmo.

**Ação (opcional):** clicar também na tabela `item_pedido` e apontar os itens
daquele pedido.

---

## 2:25 – 2:50 — Testes e fechamento

**Tela:** terminal.

**Ação:** rodar
```
./EXECUTE-AQUI.sh test
```

**Fala:**
> E pra fechar, os 28 testes automatizados, todos passando — cobrem tanto os
> casos de sucesso quanto os de erro, tipo tentar criar um pedido sem itens.

**Tela:** parado no resultado `28 passed`.

**Fala:**
> Essa foi a Fase 1. Nas próximas duas fases eu vou adicionar a gestão de
> cardápio com o fluxo de status do pedido, e depois login com perfis e
> relatórios. Obrigada!

---

## Dicas de gravação

- Fale um pouco mais devagar do que o normal — no vídeo sempre parece mais
  rápido do que parece na hora.
- Se travar numa parte, pausa a gravação, respira e regrava só aquele trecho
  (dá pra cortar depois).
- Não precisa decorar a fala palavra por palavra — usa esse roteiro como guia
  e fala com as suas palavras.
