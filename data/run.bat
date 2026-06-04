@echo off
REM Script para ejecutar SiigoBot con Streamlit en Windows
REM Nota: Ejecuta init.bat una sola vez antes de usar este script
REM Uso: run.bat

cls
echo.
echo ================================================================================
echo 🚀 RDNC BOT - Sistema de Automatizacion
echo ================================================================================
echo.



echo.
echo ✓ Verificando uv...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo   'uv' no encontrado. Instalando...
    powershell.exe -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo ✗ Error al instalar uv
        pause
        exit /b 1
    )
)

echo ✓ Sincronizando código con Git remoto...
git fetch --all --prune
if %errorlevel% neq 0 (
    echo ✗ Error al ejecutar git fetch
    pause
    exit /b 1
)

for /f "delims=" %%A in ('git rev-parse --abbrev-ref HEAD') do set "CURRENT_BRANCH=%%A"
git pull --ff-only origin %CURRENT_BRANCH%
if %errorlevel% neq 0 (
    echo ✗ Error al hacer git pull --ff-only
    pause
    exit /b 1
)

echo.
echo ✓ Sincronizando dependencias con uv sync...
uv sync
if %errorlevel% neq 0 (
    echo ✗ Error al sincronizar dependencias con uv
    pause
    exit /b 1
)

echo.
echo ✓ Iniciando aplicacion Streamlit...
echo.
uv run streamlit run main.py

if %errorlevel% neq 0 (
    echo.
    echo ✗ Error al ejecutar la aplicacion
    pause
    exit /b 1
)
