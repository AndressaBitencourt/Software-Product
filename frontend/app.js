"use strict";

const API = "/api";
const CARRINHO_KEY = "hamburgueria_carrinho";
let cardapio = [];
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

function mostrarToast(msg) {
  const el = $("#toast");
  if (!el) return;
  el.textContent = msg;
  el.hidden = false;
  el.classList.add("mostrar");
  clearTimeout(el.__timer);
  el.__timer = setTimeout(() => {
    el.classList.remove("mostrar");
    el.hidden = true;
  }, 2000);
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

function lerCarrinho() {
  try {
    return JSON.parse(localStorage.getItem(CARRINHO_KEY)) || [];
  } catch {
    return [];
  }
}

function salvarCarrinho(carrinho) {
  localStorage.setItem(CARRINHO_KEY, JSON.stringify(carrinho));
}

function atualizarContadorCarrinho() {
  const badge = $("#carrinho-contador");
  if (!badge) return;
  const total = lerCarrinho().reduce((soma, item) => soma + item.quantidade, 0);
  badge.textContent = total;
  badge.hidden = total === 0;
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
  const carrinho = lerCarrinho();
  const existente = carrinho.find((i) => i.produto_id === produtoId);
  if (existente) existente.quantidade += 1;
  else
    carrinho.push({
      produto_id: prod.id,
      nome: prod.nome,
      preco: prod.preco,
      quantidade: 1,
    });
  salvarCarrinho(carrinho);
  atualizarContadorCarrinho();
  mostrarToast(`${prod.nome} adicionado ao carrinho!`);
}

$(".carrossel-anterior").addEventListener("click", () => {
  slideAnteriorCarrossel();
  iniciarCarrossel();
});
$(".carrossel-proxima").addEventListener("click", () => {
  proximoSlideCarrossel();
  iniciarCarrossel();
});
initMenu();
atualizarContadorCarrinho();

(async function iniciar() {
  try {
    await carregarCardapio();
  } catch (e) {
    aviso("Falha ao carregar o cardápio: " + e.message, "erro");
  }
})();
