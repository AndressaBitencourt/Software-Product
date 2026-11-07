"use strict";

const API = "/api";
const CARRINHO_KEY = "hamburgueria_carrinho";

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

function renderCarrinho() {
  const carrinho = lerCarrinho();
  const ul = $("#itens-carrinho");
  ul.innerHTML = "";
  let total = 0;
  carrinho.forEach((item, idx) => {
    total += Number(item.preco) * item.quantidade;
    const li = document.createElement("li");
    li.innerHTML = `
      <span>${esc(item.nome)}</span>
      <input type="number" min="1" value="${item.quantidade}" />
      <span class="subtotal">${brl(Number(item.preco) * item.quantidade)}</span>
      <button type="button" class="perigo">x</button>`;
    li.querySelector("input").addEventListener("change", (e) => {
      const q = parseInt(e.target.value, 10);
      const atual = lerCarrinho();
      atual[idx].quantidade = Number.isNaN(q) || q < 1 ? 1 : q;
      salvarCarrinho(atual);
      renderCarrinho();
      atualizarContadorCarrinho();
    });
    li.querySelector("button").addEventListener("click", () => {
      const atual = lerCarrinho();
      atual.splice(idx, 1);
      salvarCarrinho(atual);
      renderCarrinho();
      atualizarContadorCarrinho();
    });
    ul.appendChild(li);
  });
  const vazio = carrinho.length === 0;
  $("#carrinho-vazio").hidden = !vazio;
  $("#secao-finalizar").hidden = vazio;
  $("#carrinho-total").textContent = brl(total.toFixed(2));
}

async function finalizar(evento) {
  evento.preventDefault();
  const carrinho = lerCarrinho();
  if (carrinho.length === 0) return;
  const payload = {
    cliente_nome: $("#cliente_nome").value.trim(),
    observacao: $("#observacao").value.trim() || null,
    itens: carrinho.map((i) => ({
      produto_id: i.produto_id,
      quantidade: i.quantidade,
    })),
  };
  try {
    const pedido = await api("/pedidos", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    salvarCarrinho([]);
    atualizarContadorCarrinho();
    $("#secao-carrinho").hidden = true;
    $("#secao-finalizar").hidden = true;
    $("#secao-confirmacao").hidden = false;
    $("#confirmacao-nome").textContent = pedido.cliente_nome;
    $("#confirmacao-numero").textContent = `#${pedido.id}`;
    $("#confirmacao-total").textContent = brl(pedido.total);
  } catch (e) {
    aviso(e.message, "erro");
  }
}

$("#form-finalizar").addEventListener("submit", finalizar);
initMenu();
atualizarContadorCarrinho();
renderCarrinho();
