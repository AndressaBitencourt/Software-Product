"use strict";

const API = "/api";
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

function entrarModoEdicao(produto) {
  editandoId = produto.id;
  $("#form-titulo").textContent = `Editar produto #${produto.id}`;
  $("#btn-salvar").textContent = "Salvar alterações";
  $("#btn-cancelar").hidden = false;
  $("#nome").value = produto.nome;
  $("#descricao").value = produto.descricao ?? "";
  $("#preco").value = produto.preco;
  $("#categoria").value = produto.categoria;
  $("#disponivel").checked = produto.disponivel;
  $("#secao-form").scrollIntoView({ behavior: "smooth" });
}

function sairModoEdicao() {
  editandoId = null;
  $("#form-titulo").textContent = "Novo produto";
  $("#btn-salvar").textContent = "Salvar produto";
  $("#btn-cancelar").hidden = true;
  $("#form-produto").reset();
  $("#disponivel").checked = true;
}

async function submeter(evento) {
  evento.preventDefault();
  const payload = {
    nome: $("#nome").value.trim(),
    descricao: $("#descricao").value.trim() || null,
    preco: $("#preco").value,
    categoria: $("#categoria").value.trim(),
    disponivel: $("#disponivel").checked,
  };
  try {
    if (editandoId) {
      await api(`/produtos/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      aviso("Produto atualizado.", "ok");
    } else {
      await api("/produtos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      aviso("Produto criado.", "ok");
    }
    sairModoEdicao();
    await carregarProdutos();
  } catch (e) {
    aviso(e.message, "erro");
  }
}

async function carregarProdutos() {
  const produtos = await api("/produtos?incluir_indisponiveis=true");
  const tbody = $("#lista-produtos");
  tbody.innerHTML = "";
  $("#produtos-vazio").hidden = produtos.length > 0;
  for (const p of produtos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.nome}</td>
      <td>${p.categoria}</td>
      <td>${brl(p.preco)}</td>
      <td>${p.disponivel ? "Sim" : "Não"}</td>
      <td></td>`;
    const acoes = tr.lastElementChild;

    const bEditar = document.createElement("button");
    bEditar.textContent = "Editar";
    bEditar.addEventListener("click", () => entrarModoEdicao(p));

    const bExcluir = document.createElement("button");
    bExcluir.textContent = "Excluir";
    bExcluir.className = "perigo";
    bExcluir.addEventListener("click", async () => {
      if (!confirm(`Excluir o produto "${p.nome}"?`)) return;
      try {
        await api(`/produtos/${p.id}`, { method: "DELETE" });
        aviso("Produto excluído.", "ok");
        await carregarProdutos();
      } catch (e) {
        aviso(e.message, "erro");
      }
    });

    acoes.append(bEditar, bExcluir);
    tbody.appendChild(tr);
  }
}

$("#form-produto").addEventListener("submit", submeter);
$("#btn-cancelar").addEventListener("click", sairModoEdicao);

(async function iniciar() {
  try {
    await carregarProdutos();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
