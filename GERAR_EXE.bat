@echo off
cd /d "%~dp0"
rem Gera dist\ResetAlmofadasEpson.exe (requer o INSTALAR.bat ja executado)
".venv\Scripts\python.exe" -m pip install pyinstaller --quiet
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --workpath .build-tmp --distpath dist build_exe.spec
pause
