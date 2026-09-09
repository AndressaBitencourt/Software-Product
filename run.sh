#!/usr/bin/env bash
# ============================================================================
#  Software-Product - Fase 1 (sistema de pedidos da hamburgueria)
#  Sobe o app e abre o navegador.  Para rodar os 28 testes:  ./run.sh test
#  O script verifica o Python, instala o que faltar e explica cada passo.
# ============================================================================
set -uo pipefail

PORT=8000
URL="http://localhost:$PORT"

cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "=================================================================="
echo "  SOFTWARE-PRODUCT - Fase 1"
echo "  Pasta: $ROOT"
echo "=================================================================="
echo

fail() {
  echo
  echo "================================================================"
  echo "  PAROU AQUI. O que falta / como resolver:"
  echo
  echo "  $1"
  echo "================================================================"
  echo
  exit 1
}

[ -f "$ROOT/backend/requirements.txt" ] || fail "Nao encontrei a pasta 'backend'. Extraia tudo e deixe o run.sh na mesma pasta que 'backend' e 'frontend'."
cd "$ROOT/backend"

# ------------------------------------------------------------------ [1/5] Python
echo "[1/5] Procurando o Python (>= 3.10)..."
PY=""
for c in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done

if [ -z "$PY" ]; then
  echo "      Python 3.10+ nao encontrado. Tentando instalar automaticamente..."
  echo
  if [ "$(uname)" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      brew install python@3.12 || true
    else
      echo "      O Homebrew nao esta instalado (seria o instalador automatico no Mac)."
      echo "      Abrindo a pagina oficial do Python..."
      open "https://www.python.org/downloads/" 2>/dev/null || true
      fail "Instale o Python 3.12 de python.org (ou instale o Homebrew e rode de novo), depois rode o run.sh outra vez."
    fi
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip || true
  else
    fail "Nao sei instalar o Python automaticamente neste sistema. Instale o Python 3.10+ e rode o run.sh de novo."
  fi
  for c in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
      PY="$c"; break
    fi
  done
  [ -n "$PY" ] || fail "O Python foi instalado mas nao apareceu no PATH desta sessao. Feche o terminal, abra de novo e rode o run.sh mais uma vez."
fi
echo "      OK - $("$PY" --version)   (comando: $PY)"
echo

# -------------------------------------------------------------------- [2/5] venv
echo "[2/5] Preparando o ambiente virtual (.venv)..."
if [ ! -x ".venv/bin/python" ]; then
  echo "      Criando pela primeira vez - pode demorar 1-2 min..."
  "$PY" -m venv .venv || fail "Falha ao criar o .venv. No Linux pode faltar o pacote: sudo apt-get install python3-venv"
fi
[ -x ".venv/bin/python" ] || fail "O .venv nao foi criado. Rode na mao, dentro de 'backend':  $PY -m venv .venv"
VENV_PY="./.venv/bin/python"
echo "      OK"
echo

# ------------------------------------------------------------ [3/5] dependencias
echo "[3/5] Instalando dependencias (fastapi, uvicorn, sqlalchemy, pydantic...)..."
"$VENV_PY" -m pip install --quiet --upgrade pip
if ! "$VENV_PY" -m pip install -r requirements.txt; then
  fail "O pip falhou ao instalar as dependencias (veja o erro acima). Quase sempre e falta de internet, ou proxy/firewall bloqueando o pypi.org."
fi
echo "      OK"
echo

# -------------------------------------------------------------------- [4/5] porta
echo "[4/5] Checando a porta $PORT..."
if command -v lsof >/dev/null 2>&1 && lsof -ti "tcp:$PORT" >/dev/null 2>&1; then
  echo "      AVISO: ja tem algo ouvindo na porta $PORT."
  echo "             Se for uma execucao anterior deste app, encerre com:"
  echo "             lsof -ti tcp:$PORT | xargs kill"
else
  echo "      OK - porta livre"
fi
echo

# ----------------------------------------------------------- [5/5] rodar/testar
if [ "${1:-}" = "test" ]; then
  echo "[5/5] Rodando os 28 testes..."
  echo
  exec "$VENV_PY" -m pytest -v
fi

echo "[5/5] Subindo o servidor..."
echo
echo "================================================================"
echo "  App:   $URL"
echo "  API:   $URL/docs"
echo "  Parar: Ctrl+C"
echo "================================================================"
echo

# abre o navegador ~3s depois (tempo do servidor subir)
(
  sleep 3
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
  fi
) >/dev/null 2>&1 &

exec "$VENV_PY" -m uvicorn app.main:app --port "$PORT"
