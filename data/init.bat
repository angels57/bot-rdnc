@echo off
REM Script simple para clonar repo y configurar entorno
REM Edita las variables abajo con tus valores

cls
echo.
echo ================================================================================
echo 🚀 SIIGO BOT - Inicializacion
echo ================================================================================
echo.

REM ===== VARIABLES A EDITAR =====
set "REPO_URL=https://github.com/proyectoimpocoma/bot-rdnc.git"
set "GIT_USER=proyectoimpocoma"
set "GIT_TOKEN=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"
set "GIT_BRANCH=psi_version"
REM ================================

echo Repositorio: %REPO_URL%
echo Usuario: %GIT_USER%
echo Rama: %GIT_BRANCH%
echo.

REM Verificar e instalar Git Credential Manager si no existe
echo ✓ Verificando Git Credential Manager...
git credential-manager --version >nul 2>nul
if %errorlevel% neq 0 (
    echo   No encontrado. Instalando...
    winget install --id GitCredentialManager.GitCredentialManager -e >nul 2>nul
    if %errorlevel% neq 0 (
        echo   ⚠️  No se pudo instalar automáticamente. Continuando sin él...
    ) else (
        echo   ✓ Instalado correctamente.
    )
) else (
    echo   ✓ Ya está instalado.
)

REM Construir URL con credenciales desde REPO_URL
set "REPO_PART=%REPO_URL:https://=%"
set "AUTH_URL=https://%GIT_USER%:%GIT_TOKEN%@%REPO_PART%"

echo ✓ Clonando repositorio...
git clone "%AUTH_URL%"

if %errorlevel% neq 0 (
    echo ✗ Error al clonar.
    pause
    exit /b 1
)

REM Extraer nombre del repositorio desde REPO_URL (ej: bot-rdnc)
setlocal enabledelayedexpansion
set "url=%REPO_URL%.git"
set "url=!url:.git=!"
set "REPO_NAME=!url:*/=!"
cd !REPO_NAME!

echo.
echo ✓ Cambiando a rama: %GIT_BRANCH%...
git fetch origin %GIT_BRANCH%

if %errorlevel% neq 0 (
    echo ⚠️  No se pudo hacer fetch de la rama '%GIT_BRANCH%'. Continuando con rama actual...
) else (
    git checkout %GIT_BRANCH%
    if %errorlevel% neq 0 (
        echo ⚠️  No se pudo cambiar a rama '%GIT_BRANCH%'. Continuando con rama actual...
    ) else (
        echo   ✓ Rama cambiada a: %GIT_BRANCH%
    )
)

echo ✓ Creando ambiente virtual...
python -m venv .venv

if %errorlevel% neq 0 (
    echo ✗ Error al crear ambiente virtual.
    pause
    exit /b 1
)

echo ✓ Activando ambiente virtual...
call .venv\Scripts\activate.bat

echo ✓ Instalando uv...
python -m pip install --upgrade pip >nul
python -m pip install uv >nul

if %errorlevel% neq 0 (
    echo ✗ Error al instalar uv.
    pause
    exit /b 1
)

echo ✓ Sincronizando dependencias...
python -m uv sync

if %errorlevel% neq 0 (
    echo ✗ Error al sincronizar dependencias.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo ✓ INICIALIZACION COMPLETADA
echo ================================================================================
echo.
echo Ahora ejecuta: run.bat
echo.
pause
