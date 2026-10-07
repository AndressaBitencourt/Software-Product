"use strict";

const API = "/api";
let cardapio = [];
let carrinho = []; // [{ produto_id, nome, preco, quantidade }]
let editandoId = null;
let categoriaAtiva = "Todos";
let carrosselItens = [];
let carrosselIndex = 0;
let carrosselTimer = null;

const $ = (sel) => document.querySelector(sel);

function aviso(msg, tipo) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso " + tipo;
  el.hidden = false;
  if (tipo === "ok") setTimeout(() => (el.hidden = true), 3000);
}

function brl(valorStr) {
  const n = Number(valorStr || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function initMenu() {
  const btn = $("#btn-menu");
  const menu = $("#menu-nav");
  btn.addEventListener("click", () => {
    const vaiAbrir = menu.hidden;
    menu.hidden = !vaiAbrir;
    btn.setAttribute("aria-expanded", String(vaiAbrir));
  });
  document.addEventListener("click", (e) => {
    if (!menu.hidden && !menu.contains(e.target) && e.target !== btn) {
      menu.hidden = true;
      btn.setAttribute("aria-expanded", "false");
    }
  });
}

async function api(caminho, opcoes) {
  const resp = await fetch(API + caminho, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (resp.status === 204) return null;
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detalhe = corpo.detail;
    const msg = Array.isArray(detalhe)
      ? detalhe.map((d) => d.msg).join("; ")
      : detalhe || "Erro inesperado.";
    throw new Error(msg);
  }
  return corpo;
}

function renderAbasCategoria() {
  const temPromocao = cardapio.some((p) => p.em_promocao);
  const categoriasReais = [...new Set(cardapio.map((p) => p.categoria))].sort((a, b) =>
    a.localeCompare(b, "pt-BR")
  );
  const categorias = ["Todos", ...(temPromocao ? ["Promoções"] : []), ...categoriasReais];
  if (!categorias.includes(categoriaAtiva)) categoriaAtiva = "Todos";
  const tabs = $("#categoria-tabs");
  tabs.innerHTML = "";
  for (const cat of categorias) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "categoria-tab" + (cat === categoriaAtiva ? " ativa" : "");
    btn.textContent = cat;
    btn.addEventListener("click", () => {
      categoriaAtiva = cat;
      renderAbasCategoria();
      renderCardapio();
    });
    tabs.appendChild(btn);
  }
}

function renderCardapio() {
  const box = $("#cardapio");
  box.innerHTML = "";
  const visiveis =
    categoriaAtiva === "Todos"
      ? cardapio
      : categoriaAtiva === "Promoções"
        ? cardapio.filter((p) => p.em_promocao)
        : cardapio.filter((p) => p.categoria === categoriaAtiva);
  for (const p of visiveis) {
    const div = document.createElement("div");
    div.className = "card";
    const precoHtml = p.em_promocao
      ? `<span class="preco-riscado">${brl(p.preco)}</span><span class="preco">${brl(p.preco_promocional)}</span>`
      : `<span class="preco">${brl(p.preco)}</span>`;
    const badge = p.em_promocao ? `<span class="badge-oferta">Oferta</span>` : "";
    div.innerHTML = `
      <div class="card-img-wrap">
        <img class="card-img" src="${esc(p.imagem_url || "/images/seed/placeholder.svg")}" alt="${esc(p.nome)}" />
        ${badge}
      </div>
      <div class="card-body">
        <strong>${esc(p.nome)}</strong>
        <small>${esc(p.categoria)}</small>
        <span>${esc(p.descricao ?? "")}</span>
        ${precoHtml}
        <button type="button" data-id="${p.id}">Adicionar</button>
      </div>`;
    div.querySelector("button").addEventListener("click", () => adicionar(p.id));
    box.appendChild(div);
  }
}

function pararCarrossel() {
  if (carrosselTimer) {
    clearInterval(carrosselTimer);
    carrosselTimer = null;
  }
}

function iniciarCarrossel() {
  pararCarrossel();
  if (carrosselItens.length > 1) {
    carrosselTimer = setInterval(proximoSlideCarrossel, 5000);
  }
}

function aplicarPosicaoCarrossel() {
  $("#carrossel-trilha").style.transform = `translateX(-${carrosselIndex * 100}%)`;
  document.querySelectorAll(".carrossel-dot").forEach((dot, i) => {
    dot.classList.toggle("ativo", i === carrosselIndex);
  });
}

function irParaSlideCarrossel(indice) {
  carrosselIndex = indice;
  aplicarPosicaoCarrossel();
  iniciarCarrossel();
}

function proximoSlideCarrossel() {
  carrosselIndex = (carrosselIndex + 1) % carrosselItens.length;
  aplicarPosicaoCarrossel();
}

function slideAnteriorCarrossel() {
  carrosselIndex = (carrosselIndex - 1 + carrosselItens.length) % carrosselItens.length;
  aplicarPosicaoCarrossel();
}

function renderCarrossel() {
  carrosselItens = cardapio.filter((p) => p.em_promocao);
  const secao = $("#secao-ofertas");
  if (carrosselItens.length === 0) {
    secao.hidden = true;
    pararCarrossel();
    return;
  }
  secao.hidden = false;

  const trilha = $("#carrossel-trilha");
  trilha.innerHTML = "";
  for (const p of carrosselItens) {
    const slide = document.createElement("div");
    slide.className = "carrossel-slide";
    const foto = p.imagem_url || "/images/seed/placeholder.svg";
    slide.style.backgroundImage =
      "linear-gradient(to top, rgba(20,12,8,.88), rgba(20,12,8,.25) 55%, transparent), " +
      `url("${foto.replace(/"/g, "%22")}")`;
    slide.innerHTML = `
      <div class="carrossel-info">
        <strong>${esc(p.nome)}</strong>
        <span class="preco-riscado">${brl(p.preco)}</span>
        <span class="preco">${brl(p.preco_promocional)}</span>
        <button type="button" data-id="${p.id}">Adicionar</button>
      </div>`;
    slide.querySelector("button").addEventListener("click", () => adicionar(p.id));
    trilha.appendChild(slide);
  }

  const dots = $("#carrossel-dots");
  dots.innerHTML = "";
  carrosselItens.forEach((_, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "carrossel-dot" + (i === 0 ? " ativo" : "");
    dot.setAttribute("aria-label", `Ir para oferta ${i + 1}`);
    dot.addEventListener("click", () => irParaSlideCarrossel(i));
    dots.appendChild(dot);
  });

  carrosselIndex = 0;
  aplicarPosicaoCarrossel();
  iniciarCarrossel();
}

async function carregarCardapio() {
  cardapio = await api("/produtos");
  renderAbasCategoria();
  renderCardapio();
  renderCarrossel();
}

function adicionar(produtoId) {
  const prod = cardapio.find((p) => p.id === produtoId);
  const existente = carrinho.find((i) => i.produto_id === produtoId);
  if (existente) existente.quantidade += 1;
  else
    carrinho.push({
      produto_id: prod.id,
      nome: prod.nome,
      preco: prod.preco,
      quantidade: 1,
    });
  renderCarrinho();
}

function renderCarrinho() {
  const ul = $("#carrinho");
  ul.innerHTML = "";
  let total = 0;
  carrinho.forEach((item, idx) => {
    total += Number(item.preco) * item.quantidade;
    const li = document.createElement("li");
    li.innerHTML = `
      <span>${item.nome}</span>
      <input type="number" min="1" value="${item.quantidade}" />
      <button type="button" class="perigo">x</button>`;
    li.querySelector("input").addEventListener("change", (e) => {
      const q = parseInt(e.target.value, 10);
      item.quantidade = Number.isNaN(q) || q < 1 ? 1 : q;
      renderCarrinho();
    });
    li.querySelector("button").addEventListener("click", () => {
      carrinho.splice(idx, 1);
      renderCarrinho();
    });
    ul.appendChild(li);
  });
  $("#carrinho-vazio").hidden = carrinho.length > 0;
  $("#form-total").textContent = brl(total.toFixed(2));
}

function entrarModoEdicao(pedido) {
  editandoId = pedido.id;
  $("#form-titulo").textContent = `Editar pedido #${pedido.id}`;
  $("#btn-salvar").textContent = "Salvar alterações";
  $("#btn-cancelar").hidden = false;
  $("#cliente_nome").value = pedido.cliente_nome;
  $("#observacao").value = pedido.observacao ?? "";
  carrinho = pedido.itens.map((i) => ({
    produto_id: i.produto_id,
    nome: i.produto_nome,
    preco: i.preco_unitario,
    quantidade: i.quantidade,
  }));
  renderCarrinho();
  $("#secao-form").scrollIntoView({ behavior: "smooth" });
}

function sairModoEdicao() {
  editandoId = null;
  $("#form-titulo").textContent = "Novo pedido";
  $("#btn-salvar").textContent = "Fazer pedido";
  $("#btn-cancelar").hidden = true;
  $("#form-pedido").reset();
  carrinho = [];
  renderCarrinho();
}

async function submeter(evento) {
  evento.preventDefault();
  const payload = {
    cliente_nome: $("#cliente_nome").value.trim(),
    observacao: $("#observacao").value.trim() || null,
    itens: carrinho.map((i) => ({
      produto_id: i.produto_id,
      quantidade: i.quantidade,
    })),
  };
  try {
    if (editandoId) {
      await api(`/pedidos/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      aviso("Pedido atualizado.", "ok");
    } else {
      await api("/pedidos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      aviso("Pedido criado.", "ok");
    }
    sairModoEdicao();
    await carregarPedidos();
  } catch (e) {
    aviso(e.message, "erro");
  }
}

async function carregarPedidos() {
  const pedidos = await api("/pedidos");
  const tbody = $("#lista-pedidos");
  tbody.innerHTML = "";
  $("#pedidos-vazio").hidden = pedidos.length > 0;
  for (const p of pedidos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${esc(p.cliente_nome)}</td>
      <td>${p.quantidade_itens}</td>
      <td>${brl(p.total)}</td>
      <td>${p.status}</td>
      <td>${new Date(p.criado_em).toLocaleString("pt-BR")}</td>
      <td></td>`;
    const acoes = tr.lastElementChild;

    const bVer = document.createElement("button");
    bVer.textContent = "Ver";
    bVer.className = "secundario";
    bVer.addEventListener("click", () => verDetalhe(p.id, tr));

    const bEditar = document.createElement("button");
    bEditar.textContent = "Editar";
    bEditar.addEventListener("click", async () => {
      try {
        entrarModoEdicao(await api(`/pedidos/${p.id}`));
      } catch (e) {
        aviso(e.message, "erro");
      }
    });

    const bExcluir = document.createElement("button");
    bExcluir.textContent = "Excluir";
    bExcluir.className = "perigo";
    bExcluir.addEventListener("click", async () => {
      if (!confirm(`Excluir o pedido #${p.id}?`)) return;
      try {
        await api(`/pedidos/${p.id}`, { method: "DELETE" });
        aviso("Pedido excluído.", "ok");
        await carregarPedidos();
      } catch (e) {
        aviso(e.message, "erro");
      }
    });

    acoes.append(bVer, bEditar, bExcluir);
    tbody.appendChild(tr);
  }
}

async function verDetalhe(pedidoId, linha) {
  const proxima = linha.nextElementSibling;
  if (proxima && proxima.classList.contains("detalhe-itens")) {
    proxima.remove();
    return;
  }
  try {
    const p = await api(`/pedidos/${pedidoId}`);
    const tr = document.createElement("tr");
    tr.className = "detalhe-itens";
    const linhas = p.itens
      .map(
        (i) =>
          `${i.quantidade}x ${esc(i.produto_nome)} — ${brl(i.preco_unitario)} (subtotal ${brl(i.subtotal)})`
      )
      .join("<br />");
    tr.innerHTML = `<td colspan="7">${linhas}<br /><strong>Total: ${brl(p.total)}</strong>${
      p.observacao ? "<br />Obs.: " + esc(p.observacao) : ""
    }</td>`;
    linha.after(tr);
  } catch (e) {
    aviso(e.message, "erro");
  }
}

$("#form-pedido").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);
$(".carrossel-anterior").addEventListener("click", () => {
  slideAnteriorCarrossel();
  iniciarCarrossel();
});
$(".carrossel-proxima").addEventListener("click", () => {
  proximoSlideCarrossel();
  iniciarCarrossel();
});
initMenu();

(async function iniciar() {
  try {
    await carregarCardapio();
    await carregarPedidos();
    renderCarrinho();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
