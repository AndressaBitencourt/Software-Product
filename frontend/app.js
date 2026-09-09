"use strict";

const API = "/api";
let cardapio = [];
let carrinho = []; // [{ produto_id, nome, preco, quantidade }]
let editandoId = null;

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

async function carregarCardapio() {
  cardapio = await api("/produtos");
  const box = $("#cardapio");
  box.innerHTML = "";
  for (const p of cardapio) {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <strong>${p.nome}</strong>
      <small>${p.categoria}</small>
      <span>${p.descricao ?? ""}</span>
      <span class="preco">${brl(p.preco)}</span>
      <button type="button" data-id="${p.id}">Adicionar</button>`;
    div.querySelector("button").addEventListener("click", () => adicionar(p.id));
    box.appendChild(div);
  }
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
      <td>${p.cliente_nome}</td>
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
          `${i.quantidade}x ${i.produto_nome} — ${brl(i.preco_unitario)} (subtotal ${brl(i.subtotal)})`
      )
      .join("<br />");
    tr.innerHTML = `<td colspan="7">${linhas}<br /><strong>Total: ${brl(p.total)}</strong>${
      p.observacao ? "<br />Obs.: " + p.observacao : ""
    }</td>`;
    linha.after(tr);
  } catch (e) {
    aviso(e.message, "erro");
  }
}

$("#form-pedido").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);

(async function iniciar() {
  try {
    await carregarCardapio();
    await carregarPedidos();
    renderCarrinho();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
