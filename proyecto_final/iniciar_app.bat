@echo off
REM ==========================================================================
REM  Proyecto final - Inteligencia de Negocios
REM  Doble clic para preparar el entorno (solo la primera vez) y abrir el
REM  aplicativo de redes neuronales en http://127.0.0.1:5000
REM ==========================================================================
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

set "PY="
py -3.12 --version >nul 2>nul && set "PY=py -3.12"
if not defined PY (
    python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo No se encontro Python. Instale Python 3.12 desde https://www.python.org/downloads/
    echo y marque la casilla "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo Usando: & %PY% --version

if not exist "proyecto_final\.venv\Scripts\python.exe" (
    echo Creando el entorno virtual en proyecto_final\.venv ...
    %PY% -m venv "proyecto_final\.venv"
    if errorlevel 1 ( echo No se pudo crear el entorno virtual. & pause & exit /b 1 )
)

set "VPY=proyecto_final\.venv\Scripts\python.exe"
if not exist "proyecto_final\.venv\instalado.txt" (
    echo Instalando librerias ^(la primera vez tarda varios minutos: TensorFlow pesa unos 500 MB^) ...
    "%VPY%" -m pip install --upgrade pip
    "%VPY%" -m pip install -r "proyecto_final\requirements.txt"
    if errorlevel 1 ( echo Fallo la instalacion de librerias. & pause & exit /b 1 )
    echo listo> "proyecto_final\.venv\instalado.txt"
)

echo.
echo Iniciando el aplicativo... se abrira el navegador en http://127.0.0.1:5000
echo Para cerrarlo, presione Ctrl + C en esta ventana.
start "" cmd /c "timeout /t 15 >nul & start http://127.0.0.1:5000"
"%VPY%" "proyecto_final\app\app.py"
pause
