# Roteiro do vídeo — Apresentação da Fase 2a

Roteiro para gravação de tela, ~4min30 a 5min. Fala natural, sem pressa — os
tempos abaixo são só uma referência para não passar do limite.

**A ideia central:** criar um produto novo **ao vivo**, marcado em promoção,
e mostrar ele aparecendo de verdade no carrossel de ofertas e na aba
"Promoções" da tela de Pedidos — prova que as duas telas (Pedidos e Gestão
de Cardápio) usam o mesmo banco de dados, em tempo real.

## Antes de gravar (checklist)

- [ ] Fechar abas e programas que não vão aparecer no vídeo
- [ ] Deixar só 2 janelas prontas: **navegador** (em branco, sem abrir ainda)
      e **VSCode** com o projeto aberto
- [ ] Apagar `backend/app.db` para o banco começar limpo (Finder ou
      `rm backend/app.db`) — assim o cardápio aparece com os 16 produtos do
      seed e a lista de pedidos começa vazia
- [ ] Ter o terminal do VSCode aberto na pasta do projeto
- [ ] Ter uma foto de produto separada (qualquer JPG/PNG do computador) pronta
      pra usar no upload ao vivo
- [ ] Testar o `EXECUTE-AQUI` uma vez antes de gravar, pra garantir que sobe
      sem erro

---

## 0:00 – 0:20 — Abertura

**Tela:** VSCode aberto, mostrando a raiz do projeto.

**Fala:**
> Oi, de novo! Essa é a apresentação da **Fase 2a** do meu sistema de pedidos
> da hamburgueria. Na Fase 1 eu fiz o CRUD de pedidos; nessa fase eu
> construí a **gestão de cardápio** — cadastro de produto com foto,
> categorias e um sistema de promoções — e dei uma repaginada visual
> completa na tela de pedidos.

---

## 0:20 – 0:40 — Subindo o app

**Tela:** terminal do VSCode.

**Fala:**
> Pra rodar é o mesmo script de sempre, sem precisar de Docker.

**Ação:** digitar e rodar
```
./EXECUTE-AQUI.sh
```
(ou `EXECUTE-AQUI.bat` se estiver gravando no Windows)

---

## 0:40 – 2:00 — Tela de Pedidos (o visual novo)

**Tela:** navegador em `http://localhost:8000`.

**Fala:**
> Essa é a tela de Pedidos, com a identidade visual nova — paleta de cores,
> tipografia e um menu retrátil aqui no canto, pra não ocupar espaço.

**Ação:** clicar no ☰ pra abrir o menu, mostrar os dois links (Pedidos /
Gerenciar Cardápio), fechar de novo.

**Ação:** apontar o carrossel "Ofertas do dia".

**Fala:**
> No topo tem um carrossel das ofertas do dia — os produtos que estão
> marcados em promoção aparecem aqui, com o preço original riscado e o
> preço promocional, trocando sozinho a cada alguns segundos. Dá pra
> navegar manualmente pelas setas ou pelos pontinhos também.

**Ação:** apontar as abas de categoria (Todos / Promoções / Clássicos /
Especiais / Acompanhamentos / Bebidas / Sobremesas), clicar em 2 ou 3 pra
mostrar o filtro.

**Fala:**
> Embaixo, o cardápio agora tem foto de cada produto, e dá pra filtrar por
> categoria — inclusive uma aba só de "Promoções", que puxa os mesmos itens
> do carrossel.

**Ação:** clicar em "Adicionar" em 1 ou 2 itens, preencher o nome do
cliente, clicar em "Fazer pedido" (fluxo rápido, já mostrado na Fase 1).

**Fala:**
> O fluxo de criar pedido continua o mesmo de antes, só que agora puxando
> produtos com foto e, se for o caso, com o preço promocional já aplicado.

---

## 2:00 – 3:40 — Gestão de Cardápio (o núcleo da fase)

**Tela:** abrir o menu ☰ → "Gerenciar Cardápio".

**Fala:**
> Agora vou pra tela de gestão, onde dá pra cadastrar, editar e excluir
> produto.

**Ação:** preencher o formulário de novo produto — nome, descrição, preço,
categoria (mostrar que o campo sugere categorias já existentes), marcar
"Em promoção" e preencher o preço promocional. Clicar em "Salvar produto".

**Fala:**
> Vou cadastrar um produto novo e já marcar ele em promoção — o preço
> promocional precisa ser menor que o preço normal, isso é validado no
> back-end.

**Ação:** depois de salvo, fazer o upload da foto (campo de arquivo), e
mostrar a prévia aparecendo.

**Fala:**
> A foto é enviada separado, num segundo passo — assim dá pra trocar só a
> foto sem precisar reenviar o resto dos dados do produto.

**Ação:** voltar pro menu ☰ → "Pedidos", e mostrar o produto novo aparecendo
no carrossel de ofertas e na aba "Promoções".

**Fala:**
> E aqui está a prova de que é tudo banco de dados de verdade: o produto que
> acabei de cadastrar na tela de gestão já aparece aqui no carrossel e na
> aba de Promoções, sem eu ter feito nada além de voltar pra essa tela.

**Ação:** voltar pra "Gerenciar Cardápio", tentar excluir um produto que já
está em algum pedido (vai dar erro).

**Fala:**
> Uma regra de negócio importante: um produto que já apareceu em algum
> pedido não pode ser excluído — só marcado como indisponível — pra não
> perder o histórico. O sistema bloqueia e explica o motivo.

---

## 3:40 – 4:15 — Código

**Tela:** VSCode, abrir `backend/app/models.py` (apontar os campos
`em_promocao` e `preco_promocional` no modelo `Produto`), depois
`backend/app/crud.py` (apontar a função que valida a promoção).

**Fala:**
> A arquitetura continua em camadas, como na Fase 1: modelo, schema, regra
> de negócio e router. Essa validação aqui — preço promocional obrigatório
> e menor que o preço normal — fica isolada na camada de regra de negócio,
> sem nenhuma dependência do framework web.

---

## 4:15 – 4:40 — Testes e fechamento

**Tela:** terminal.

**Ação:** rodar
```
./EXECUTE-AQUI.sh test
```

**Fala:**
> E pra fechar, os testes automatizados — já são 60 no total, cobrindo
> desde o CRUD de pedidos da Fase 1 até a validação de promoção e o upload
> de imagem dessa fase.

**Tela:** parado no resultado `60 passed`.

**Fala:**
> Essa foi a Fase 2a. Na Fase 2b eu vou trabalhar o fluxo de status do
> pedido — cozinha, conta — e depois, na última fase, login com perfis e
> relatórios. Obrigada!

---

## Dicas de gravação

- Fale um pouco mais devagar do que o normal — no vídeo sempre parece mais
  rápido do que parece na hora.
- Se travar numa parte, pausa a gravação, respira e regrava só aquele trecho
  (dá pra cortar depois).
- Não precisa decorar a fala palavra por palavra — usa esse roteiro como guia
  e fala com as suas palavras.
- Se o vídeo ficar longo demais, o trecho de código (3:40–4:15) é o mais
  fácil de cortar sem perder a demonstração funcional.
