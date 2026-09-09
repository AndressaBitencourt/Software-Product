#!/usr/bin/env bash
# Sobe o app da hamburgueria. Para rodar os testes em vez do servidor: ./run.sh test
set -euo pipefail

cd "$(dirname "$0")/backend"

# 1. Encontra o Python
PY=""
for c in python3.12 python3 python; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "ERRO: Python nao encontrado. Instale Python 3.12+ de https://python.org"
  exit 1
fi

# 2. Versao minima 3.10 (recomendado 3.12)
if ! "$PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "ERRO: precisa de Python 3.10+ (recomendado 3.12). Atual: $("$PY" --version)"
  exit 1
fi

# 3. Cria o ambiente virtual na primeira vez
if [ ! -d .venv ]; then
  echo ">> Criando ambiente virtual (primeira vez, demora um pouco)..."
  "$PY" -m venv .venv
fi
VENV_PY="./.venv/bin/python"

# 4. Instala as dependencias
echo ">> Instalando dependencias..."
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r requirements.txt

# 5. Testes ou servidor
if [ "${1:-}" = "test" ]; then
  echo ">> Rodando os testes..."
  exec "$VENV_PY" -m pytest -v
fi

echo ""
echo "================================================================"
echo "  App no ar:  http://localhost:8000      (API / Swagger em /docs)"
echo "  Para parar: Ctrl+C"
echo "================================================================"
echo ""
exec "$VENV_PY" -m uvicorn app.main:app --port 8000
