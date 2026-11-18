@echo off
setlocal
cd /d "%~dp0"
title Instalador - Reset Almofadas Epson
echo ============================================================
echo    INSTALADOR - RESET ALMOFADAS EPSON L1250 / L3250
echo ============================================================
echo.

rem Versao fixa do motor (epson_print_conf) testada com este programa
set "COMMIT=2dc3bebacf314f22bd6484acdb2a7434c7cc00ad"

rem ---------- 1. Localizar Python 3 ----------
set "PY="
python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"

if not defined PY (
    echo [1/3] Python nao encontrado. Instalando Python 3.12...
    winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)
if not defined PY (
    echo.
    echo ERRO: nao foi possivel instalar o Python automaticamente.
    echo Instale manualmente em https://www.python.org/downloads/
    echo marcando "Add Python to PATH", e rode este instalador de novo.
    pause
    exit /b 1
)
echo [1/3] Python OK: %PY%

rem ---------- 2. Baixar o motor ----------
if exist "motor\epson_print_conf.py" (
    echo [2/3] Motor ja instalado.
) else (
    echo [2/3] Baixando motor epson_print_conf...
    curl -L -o motor.zip "https://github.com/Ircama/epson_print_conf/archive/%COMMIT%.zip"
    if errorlevel 1 goto erro
    tar -xf motor.zip
    if errorlevel 1 goto erro
    if exist motor rmdir /s /q motor
    move "epson_print_conf-%COMMIT%" motor >nul
    del motor.zip
)

rem ---------- 3. Ambiente Python e dependencias ----------
echo [3/3] Instalando dependencias (pode demorar alguns minutos)...
if not exist ".venv\Scripts\python.exe" "%PY%" -m venv .venv
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r motor\requirements.txt --quiet
if errorlevel 1 goto erro

echo.
echo ============================================================
echo  INSTALACAO CONCLUIDA! Agora execute o RESETAR.bat
echo ============================================================
pause
exit /b 0

:erro
echo.
echo ERRO durante a instalacao. Verifique a conexao com a internet
echo e execute o INSTALAR.bat novamente.
pause
exit /b 1
