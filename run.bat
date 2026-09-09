@echo off
REM Sobe o app da hamburgueria e abre o navegador. Para rodar os testes: run.bat test
setlocal enabledelayedexpansion
cd /d "%~dp0backend"

set "PORT=8000"
set "URL=http://localhost:%PORT%"

REM 1. Encontra o Python
set "PY="
for %%C in (python py) do (
  if not defined PY (
    where %%C >nul 2>nul && set "PY=%%C"
  )
)
if not defined PY (
  echo.
  echo ERRO: Python nao encontrado.
  echo Instale o Python 3.12+ de https://python.org e marque "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

REM 2. Cria o ambiente virtual na primeira vez
if not exist ".venv\" (
  echo ^>^> Criando ambiente virtual ^(primeira vez, demora um pouco^)...
  %PY% -m venv .venv
)
set "VENV_PY=.venv\Scripts\python.exe"

REM 3. Instala as dependencias
echo ^>^> Instalando dependencias...
"%VENV_PY%" -m pip install --quiet --upgrade pip
"%VENV_PY%" -m pip install --quiet -r requirements.txt

REM 4. Testes ou servidor
if /I "%~1"=="test" (
  echo ^>^> Rodando os testes...
  "%VENV_PY%" -m pytest -v
  pause
  exit /b 0
)

echo.
echo ================================================================
echo   App no ar:  %URL%      ^(API / Swagger em /docs^)
echo   Para parar: feche esta janela ou aperte Ctrl+C
echo ================================================================
echo.

REM Abre o navegador assim que o servidor subir (~3s)
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start "" %URL%"

"%VENV_PY%" -m uvicorn app.main:app --port %PORT%
pause
