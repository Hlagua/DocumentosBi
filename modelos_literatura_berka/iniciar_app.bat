@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

set "VPY=proyecto_final\.venv\Scripts\python.exe"
if not exist "%VPY%" (
    set "VPY=modelos_literatura_berka\.venv\Scripts\python.exe"
)
if not exist "%VPY%" (
    echo Creando entorno virtual en modelos_literatura_berka\.venv ...
    py -3.12 -m venv "modelos_literatura_berka\.venv" || python -m venv "modelos_literatura_berka\.venv"
    set "VPY=modelos_literatura_berka\.venv\Scripts\python.exe"
    "%VPY%" -m pip install -r "proyecto_final\requirements.txt"
)

echo Iniciando aplicativo de Literatura Berka en http://127.0.0.1:5001 ...
start "" cmd /c "timeout /t 10 >nul & start http://127.0.0.1:5001"
"%VPY%" "modelos_literatura_berka\app\app.py"
pause
