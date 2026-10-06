"use strict";

const API = "/api";
let editandoId = null;
let arquivoSelecionado = null;

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

function entrarModoEdicao(produto) {
  editandoId = produto.id;
  arquivoSelecionado = null;
  $("#imagem").value = "";
  $("#form-titulo").textContent = `Editar produto #${produto.id}`;
  $("#btn-salvar").textContent = "Salvar alterações";
  $("#btn-cancelar").hidden = false;
  $("#nome").value = produto.nome;
  $("#descricao").value = produto.descricao ?? "";
  $("#preco").value = produto.preco;
  $("#categoria").value = produto.categoria;
  $("#disponivel").checked = produto.disponivel;
  const preview = $("#preview-imagem");
  if (produto.imagem_url) {
    preview.src = produto.imagem_url;
    preview.hidden = false;
  } else {
    preview.hidden = true;
  }
  $("#secao-form").scrollIntoView({ behavior: "smooth" });
}

function sairModoEdicao() {
  editandoId = null;
  arquivoSelecionado = null;
  $("#form-titulo").textContent = "Novo produto";
  $("#btn-salvar").textContent = "Salvar produto";
  $("#btn-cancelar").hidden = true;
  $("#form-produto").reset();
  $("#disponivel").checked = true;
  $("#preview-imagem").hidden = true;
}

async function enviarImagem(produtoId, arquivo) {
  const dados = new FormData();
  dados.append("arquivo", arquivo);
  const resp = await fetch(`${API}/produtos/${produtoId}/imagem`, {
    method: "POST",
    body: dados,
  });
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(corpo.detail || "Falha ao enviar a imagem.");
  }
  return corpo;
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
  const estavaEditando = Boolean(editandoId);
  const arquivoParaEnviar = arquivoSelecionado;
  let produto;
  try {
    if (editandoId) {
      produto = await api(`/produtos/${editandoId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      produto = await api("/produtos", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
  } catch (e) {
    aviso(e.message, "erro");
    return;
  }

  sairModoEdicao();
  await carregarProdutos();

  if (!arquivoParaEnviar) {
    aviso(estavaEditando ? "Produto atualizado." : "Produto criado.", "ok");
    return;
  }

  try {
    await enviarImagem(produto.id, arquivoParaEnviar);
    aviso(estavaEditando ? "Produto atualizado." : "Produto criado.", "ok");
    await carregarProdutos();
  } catch (e) {
    aviso(
      `Produto ${estavaEditando ? "atualizado" : "criado"}, mas a foto não foi enviada: ${e.message}`,
      "erro"
    );
  }
}

function atualizarListaCategorias(produtos) {
  const categorias = [...new Set(produtos.map((p) => p.categoria))].sort();
  $("#categorias-lista").innerHTML = categorias
    .map((c) => `<option value="${c}"></option>`)
    .join("");
}

async function carregarProdutos() {
  const produtos = await api("/produtos?incluir_indisponiveis=true");
  atualizarListaCategorias(produtos);
  const tbody = $("#lista-produtos");
  tbody.innerHTML = "";
  $("#produtos-vazio").hidden = produtos.length > 0;
  for (const p of produtos) {
    const tr = document.createElement("tr");
    const foto = p.imagem_url || "/images/seed/placeholder.svg";
    tr.innerHTML = `
      <td><img class="thumb" src="${foto}" alt="${p.nome}" /></td>
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
$("#imagem").addEventListener("change", (e) => {
  const arquivo = e.target.files[0] ?? null;
  arquivoSelecionado = arquivo;
  const preview = $("#preview-imagem");
  if (arquivo) {
    preview.src = URL.createObjectURL(arquivo);
    preview.hidden = false;
  }
});
initMenu();

(async function iniciar() {
  try {
    await carregarProdutos();
  } catch (e) {
    aviso("Falha ao carregar dados: " + e.message, "erro");
  }
})();
