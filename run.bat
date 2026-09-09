@echo off
REM ============================================================================
REM  Software-Product - Fase 1 (sistema de pedidos da hamburgueria)
REM  Sobe o app.  Para rodar os 28 testes em vez do servidor:  run.bat test
REM  O script verifica o Python, instala o que faltar e explica cada passo.
REM ============================================================================
setlocal enabledelayedexpansion
title Software-Product - setup e execucao

set "PORT=8000"
set "URL=http://localhost:%PORT%"
set "TRIED_INSTALL="

cd /d "%~dp0"
set "ROOT=%CD%"

echo ==================================================================
echo   SOFTWARE-PRODUCT - Fase 1
echo   Pasta: %ROOT%
echo ==================================================================
echo.

if not exist "%ROOT%\backend\requirements.txt" (
  set "ERR=Nao encontrei a pasta 'backend' aqui. Extraia o ZIP inteiro e mantenha o run.bat na mesma pasta que 'backend' e 'frontend'."
  goto :fail
)
cd /d "%ROOT%\backend"

REM ---------------------------------------------------------------- [1/5] Python
echo [1/5] Procurando o Python...
call :find_python
if not defined PY (
  echo       Python NAO encontrado nesta maquina.
  echo       Tentando instalar automaticamente...
  echo.
  set "TRIED_INSTALL=1"
  call :install_python
  echo.
  call :find_python
)
if not defined PY (
  if defined TRIED_INSTALL (
    set "ERR=O Python foi (ou tentou ser) instalado, mas esta janela ainda nao enxerga. FECHE esta janela, abra de novo e rode o run.bat mais uma vez. Se continuar, instale manualmente de https://www.python.org/downloads/ marcando 'Add python.exe to PATH'."
  ) else (
    set "ERR=Python nao esta instalado. Baixe de https://www.python.org/downloads/ e MARQUE 'Add python.exe to PATH' na instalacao."
  )
  goto :fail
)
echo       OK - !PYVERSION!   ^(comando: !PY!^)
echo.

REM ------------------------------------------------------------------ [2/5] venv
echo [2/5] Preparando o ambiente virtual (.venv)...
if not exist ".venv\Scripts\python.exe" (
  echo       Criando pela primeira vez - pode demorar 1-2 min...
  !PY! -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  set "ERR=Nao consegui criar o .venv. Rode na mao, dentro da pasta 'backend':   !PY! -m venv .venv"
  goto :fail
)
set "VENV_PY=.venv\Scripts\python.exe"
echo       OK
echo.

REM ---------------------------------------------------------- [3/5] dependencias
echo [3/5] Instalando dependencias (fastapi, uvicorn, sqlalchemy, pydantic...)...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>&1
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  set "ERR=O pip falhou ao instalar as dependencias (veja o erro acima). Quase sempre e falta de internet, ou um proxy/firewall bloqueando o acesso ao pypi.org."
  goto :fail
)
echo       OK
echo.

REM ------------------------------------------------------------------ [4/5] porta
echo [4/5] Checando a porta %PORT%...
netstat -ano | findstr ":%PORT%" | findstr /i "LISTENING" >nul
if not errorlevel 1 (
  echo       AVISO: ja existe um programa ouvindo na porta %PORT%.
  echo              Se for uma execucao anterior deste app, feche-a antes,
  echo              senao o navegador vai abrir a instancia antiga.
) else (
  echo       OK - porta livre
)
echo.

REM ------------------------------------------------------------ [5/5] rodar/testar
if /I "%~1"=="test" (
  echo [5/5] Rodando os 28 testes...
  echo.
  "%VENV_PY%" -m pytest -v
  echo.
  echo ^(fim dos testes^)
  pause
  exit /b 0
)

echo [5/5] Subindo o servidor...
echo.
echo ================================================================
echo   App:   %URL%
echo   API:   %URL%/docs
echo   Parar: feche esta janela ou aperte Ctrl+C
echo ================================================================
echo.
start "" /b cmd /c "timeout /t 4 /nobreak >nul & start %URL%"
"%VENV_PY%" -m uvicorn app.main:app --port %PORT%
echo.
echo ^(o servidor foi encerrado^)
pause
exit /b 0


REM ============================ sub-rotinas ============================

:find_python
set "PY="
set "PYVERSION="
for /f "tokens=*" %%v in ('py -3 --version 2^>nul') do set "PYVERSION=%%v"
if defined PYVERSION ( set "PY=py -3" & goto :eof )
for /f "tokens=*" %%v in ('python --version 2^>nul') do set "PYVERSION=%%v"
if defined PYVERSION (
  echo !PYVERSION! | findstr /i /c:"Python 3" >nul && set "PY=python"
)
if not defined PY set "PYVERSION="
goto :eof

:install_python
where winget >nul 2>nul
if errorlevel 1 (
  echo       O 'winget' nao esta disponivel neste Windows - nao da pra instalar sozinho.
  echo       Abrindo a pagina oficial de download no navegador...
  start "" "https://www.python.org/downloads/"
  echo       Instale, MARQUE "Add python.exe to PATH", feche esta janela e rode o run.bat de novo.
  goto :eof
)
echo       Instalando o Python 3.12 via winget (pode aparecer uma confirmacao)...
winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
echo       Atualizando o PATH desta sessao...
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
  if exist "%%d\python.exe" set "PATH=%%d;%%d\Scripts;!PATH!"
)
if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" set "PATH=%LOCALAPPDATA%\Programs\Python\Launcher;!PATH!"
goto :eof

:fail
echo.
echo ================================================================
echo   PAROU AQUI. O que falta / como resolver:
echo.
echo   !ERR!
echo ================================================================
echo.
pause
exit /b 1
