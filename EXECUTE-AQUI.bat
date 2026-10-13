@echo off
REM ============================================================================
REM  Software-Product - Fase 1 (sistema de pedidos da hamburgueria)
REM  Sobe o app.  Para rodar os 28 testes em vez do servidor:  EXECUTE-AQUI.bat test
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
  set "ERR=Nao encontrei a pasta 'backend' aqui. Extraia o ZIP inteiro e mantenha o EXECUTE-AQUI.bat na mesma pasta que 'backend' e 'frontend'."
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
    set "ERR=O Python foi (ou tentou ser) instalado, mas esta janela ainda nao enxerga. FECHE esta janela, abra de novo e rode o EXECUTE-AQUI.bat mais uma vez. Se continuar, instale manualmente de https://www.python.org/downloads/ marcando 'Add python.exe to PATH'."
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
call :free_port
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

REM cache-buster: cada execucao abre uma URL diferente, entao o navegador
REM nunca reaproveita HTML/CSS/JS antigos em cache de uma execucao anterior.
set "CACHEBUST=%RANDOM%%RANDOM%"
set "OPEN_URL=%URL%/?v=%CACHEBUST%"

echo [5/5] Subindo o servidor...
echo.
echo ================================================================
echo   App:   %URL%
echo   API:   %URL%/docs
echo   Parar: feche esta janela ou aperte Ctrl+C
echo ================================================================
echo.
call :open_browser
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
  echo       Instale, MARQUE "Add python.exe to PATH", feche esta janela e rode o EXECUTE-AQUI.bat de novo.
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

REM Mata quem estiver ouvindo em %PORT% (so se for um processo python.exe -
REM ou seja, uma execucao anterior deste mesmo app) e espera a porta liberar.
REM Assim, rodar o EXECUTE-AQUI.bat duas vezes nunca deixa duas instancias
REM do servidor no ar nem abre o navegador apontando pra uma instancia velha.
:free_port
set "FREED="
set "BLOCKED_BY_OUTRO="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
  set "PID=%%p"
  set "PNAME="
  for /f "tokens=1" %%n in ('tasklist /fi "PID eq !PID!" /nh 2^>nul') do set "PNAME=%%n"
  echo !PNAME! | findstr /i "python" >nul
  if not errorlevel 1 (
    echo       Encerrando uma execucao anterior deste app ^(PID !PID!^)...
    taskkill /F /PID !PID! >nul 2>&1
    set "FREED=1"
  ) else if defined PNAME (
    echo       AVISO: a porta %PORT% esta em uso por "!PNAME!" ^(PID !PID!^), que nao parece ser este app.
    echo              Feche esse programa manualmente se a porta continuar ocupada.
    set "BLOCKED_BY_OUTRO=1"
  )
)
if defined FREED (
  REM espera o Windows liberar a porta de verdade (ate ~5s)
  for /l %%i in (1,1,5) do (
    netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul
    if errorlevel 1 ( goto :free_port_done )
    timeout /t 1 /nobreak >nul
  )
)
:free_port_done
if defined BLOCKED_BY_OUTRO ( echo       (seguindo mesmo assim - pode falhar ao subir^) ) else ( echo       OK - porta livre )
goto :eof

REM Abre o navegador numa janela anonima/privada (quando acha Edge ou Chrome
REM instalado), pra nunca servir HTML/CSS/JS antigos do cache do navegador.
REM Se nao achar nenhum dos dois, cai pro navegador padrao mesmo assim -
REM a URL com cache-buster ja evita a maior parte do problema.
:open_browser
set "BROWSER_EXE="
set "BROWSER_FLAG="
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  set "BROWSER_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
  set "BROWSER_FLAG=--inprivate"
)
if not defined BROWSER_EXE if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  set "BROWSER_EXE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
  set "BROWSER_FLAG=--inprivate"
)
if not defined BROWSER_EXE if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  set "BROWSER_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  set "BROWSER_FLAG=--incognito"
)
if not defined BROWSER_EXE if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  set "BROWSER_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
  set "BROWSER_FLAG=--incognito"
)
if not defined BROWSER_EXE if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
  set "BROWSER_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
  set "BROWSER_FLAG=--incognito"
)
if defined BROWSER_EXE (
  start "" /b cmd /c "timeout /t 4 /nobreak >nul & "!BROWSER_EXE!" !BROWSER_FLAG! !OPEN_URL!"
) else (
  start "" /b cmd /c "timeout /t 4 /nobreak >nul & start !OPEN_URL!"
)
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
