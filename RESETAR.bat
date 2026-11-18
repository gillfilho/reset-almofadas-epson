@echo off
cd /d "%~dp0"
title Reset Almofadas Epson L1250 / L3250
if not exist ".venv\Scripts\python.exe" (
    echo Programa ainda nao instalado. Execute primeiro o INSTALAR.bat
    pause
    exit /b 1
)
".venv\Scripts\python.exe" reset_almofadas.py %*
pause
