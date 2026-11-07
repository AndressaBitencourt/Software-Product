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

async function fetchJson(url) {
  const resp = await fetch(url);
  if (resp.status === 401) {
    window.location.href = "/login.html";
    throw new Error("Sessão expirada.");
  }
  return resp.json();
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
  const corpo = await fetchJson(`${API}/relatorios/resumo?${periodoSelecionado()}`);
  $("#resumo-total-pedidos").textContent = corpo.total_pedidos;
  $("#resumo-faturamento").textContent = brl(corpo.faturamento_total);
  $("#resumo-ticket-medio").textContent = brl(corpo.ticket_medio);
}

const PALETA_PRODUTOS = [
  "#F0A94E", "#E8574B", "#4FB6A8", "#8C6FD1", "#5AA7E0",
  "#C2D34E", "#E06BA8", "#F2C14E", "#6FD1A5", "#D97B4F",
];

async function carregarGraficoFaturamento() {
  const dados = await fetchJson(
    `${API}/relatorios/faturamento-diario?${periodoSelecionado()}`
  );
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
          backgroundColor: (contexto) => {
            const { chartArea, ctx: canvasCtx } = contexto.chart;
            if (!chartArea) return "#E8A33D";
            const gradiente = canvasCtx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradiente.addColorStop(0, "#F0A94E");
            gradiente.addColorStop(1, "#C23B52");
            return gradiente;
          },
          borderRadius: 6,
          maxBarThickness: 46,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (item) => brl(item.parsed.y) } },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#cfc4dd" },
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.08)" },
          ticks: { color: "#cfc4dd", callback: (valor) => brl(valor) },
        },
      },
    },
  });
}

async function carregarGraficoProdutos() {
  const dados = await fetchJson(
    `${API}/relatorios/produtos-mais-vendidos?${periodoSelecionado()}`
  );
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
          backgroundColor: dados.map((_, i) => PALETA_PRODUTOS[i % PALETA_PRODUTOS.length]),
          borderRadius: 6,
          maxBarThickness: 28,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.08)" },
          ticks: { color: "#cfc4dd" },
        },
        y: {
          grid: { display: false },
          ticks: { color: "#cfc4dd" },
        },
      },
    },
  });
}

async function buscarPedidos() {
  const params = periodoSelecionado();
  const cliente = $("#busca-cliente").value.trim();
  if (cliente) params.set("cliente_nome", cliente);
  const pedidos = await fetchJson(`${API}/pedidos?${params}`);
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
  const hoje = new Date();
  const trintaDiasAtras = new Date(hoje);
  trintaDiasAtras.setDate(hoje.getDate() - 30);
  $("#data_fim").value = hoje.toISOString().slice(0, 10);
  $("#data_inicio").value = trintaDiasAtras.toISOString().slice(0, 10);
  await recarregarTudo();
})();
