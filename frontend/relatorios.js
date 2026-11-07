"use strict";

const API = "/api";
let graficoFaturamento = null;
let graficoProdutos = null;

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
    window.location.href = "/";
    return null;
  }
  return usuario;
}

function aplicarUsuarioNoMenu(usuario) {
  $("#usuario-nome").textContent = usuario.nome;
  $("#btn-sair").addEventListener("click", async () => {
    await fetch(`${API}/logout`, { method: "POST" });
    window.location.href = "/login.html";
  });
}

function periodoSelecionado() {
  const inicio = $("#data_inicio").value;
  const fim = $("#data_fim").value;
  const params = new URLSearchParams();
  if (inicio) params.set("data_inicio", `${inicio}T00:00:00Z`);
  if (fim) params.set("data_fim", `${fim}T23:59:59Z`);
  return params;
}

async function carregarResumo() {
  const resp = await fetch(`${API}/relatorios/resumo?${periodoSelecionado()}`);
  const corpo = await resp.json();
  $("#resumo-total-pedidos").textContent = corpo.total_pedidos;
  $("#resumo-faturamento").textContent = brl(corpo.faturamento_total);
  $("#resumo-ticket-medio").textContent = brl(corpo.ticket_medio);
}

async function carregarGraficoFaturamento() {
  const resp = await fetch(
    `${API}/relatorios/faturamento-diario?${periodoSelecionado()}`
  );
  const dados = await resp.json();
  const ctx = $("#grafico-faturamento");
  if (graficoFaturamento) graficoFaturamento.destroy();
  graficoFaturamento = new Chart(ctx, {
    type: "bar",
    data: {
      labels: dados.map((d) => d.data),
      datasets: [
        {
          label: "Faturamento (R$)",
          data: dados.map((d) => Number(d.total)),
          backgroundColor: "#E8A33D",
        },
      ],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

async function carregarGraficoProdutos() {
  const resp = await fetch(
    `${API}/relatorios/produtos-mais-vendidos?${periodoSelecionado()}`
  );
  const dados = await resp.json();
  const ctx = $("#grafico-produtos");
  if (graficoProdutos) graficoProdutos.destroy();
  graficoProdutos = new Chart(ctx, {
    type: "bar",
    data: {
      labels: dados.map((d) => d.produto_nome),
      datasets: [
        {
          label: "Quantidade vendida",
          data: dados.map((d) => d.quantidade_total),
          backgroundColor: "#7A1F1F",
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });
}

async function buscarPedidos() {
  const params = periodoSelecionado();
  const cliente = $("#busca-cliente").value.trim();
  if (cliente) params.set("cliente_nome", cliente);
  const resp = await fetch(`${API}/pedidos?${params}`);
  const pedidos = await resp.json();
  const tbody = $("#lista-pedidos-busca");
  tbody.innerHTML = "";
  $("#busca-vazia").hidden = pedidos.length > 0;
  for (const p of pedidos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${esc(p.cliente_nome)}</td>
      <td>${p.quantidade_itens}</td>
      <td>${brl(p.total)}</td>
      <td>${p.status}</td>
      <td>${new Date(p.criado_em).toLocaleString("pt-BR")}</td>`;
    tbody.appendChild(tr);
  }
}

async function recarregarTudo() {
  try {
    await Promise.all([
      carregarResumo(),
      carregarGraficoFaturamento(),
      carregarGraficoProdutos(),
      buscarPedidos(),
    ]);
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
}

$("#form-filtro").addEventListener("submit", (e) => {
  e.preventDefault();
  recarregarTudo();
});
$("#form-busca").addEventListener("submit", (e) => {
  e.preventDefault();
  buscarPedidos();
});
initMenu();

(async function iniciar() {
  const usuario = await verificarSessao("admin");
  if (!usuario) return;
  aplicarUsuarioNoMenu(usuario);
  await recarregarTudo();
})();
