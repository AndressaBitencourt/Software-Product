"use strict";

const API = "/api";
const $ = (sel) => document.querySelector(sel);

function aviso(msg, tipo) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso " + tipo;
  el.hidden = false;
}

$("#form-login").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const email = $("#email").value.trim();
  const senha = $("#senha").value;
  try {
    const resp = await fetch(`${API}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    if (!resp.ok) {
      const corpo = await resp.json().catch(() => ({}));
      throw new Error(corpo.detail || "E-mail ou senha inválidos.");
    }
    window.location.href = "/painel-pedidos.html";
  } catch (e) {
    aviso(e.message, "erro");
  }
});
