"use strict";

const API = "/api";

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

async function verificarSessao(papelExigido) {
  const resp = await fetch(`${API}/me`);
  if (resp.status === 401) {
    window.location.href = "/login.html";
    return null;
  }
  const usuario = await resp.json();
  if (papelExigido && usuario.papel !== papelExigido) {
    window.location.href = "/painel-pedidos.html";
    return null;
  }
  return usuario;
}

function aplicarUsuarioNoMenu(usuario) {
  $("#usuario-nome").textContent = usuario.nome;
  const linkCardapio = $("#link-cardapio");
  const linkRelatorios = $("#link-relatorios");
  if (linkCardapio) linkCardapio.hidden = usuario.papel !== "admin";
  if (linkRelatorios) linkRelatorios.hidden = usuario.papel !== "admin";
  $("#btn-sair").addEventListener("click", async () => {
    await fetch(`${API}/logout`, { method: "POST" });
    window.location.href = "/login.html";
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

    acoes.append(bVer, bExcluir);
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

initMenu();

(async function iniciar() {
  const usuario = await verificarSessao();
  if (!usuario) return;
  aplicarUsuarioNoMenu(usuario);
  try {
    await carregarPedidos();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
