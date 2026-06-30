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
set "GITHUB_T=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"
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
set "AUTH_URL=https://%GIT_USER%:%GITHUB_T%@%REPO_PART%"

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
