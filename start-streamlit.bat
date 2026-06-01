@echo off
REM Script de inicio para Streamlit con proxy inverso IIS
REM Uso: start-streamlit.bat

setlocal enabledelayedexpansion

REM Variables de entorno para Streamlit
set PYTHONUNBUFFERED=1
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_SERVER_BASEURL=https://impocoma.com.co:8084/cotizacion
set STREAMLIT_SERVER_BASEurlpath=/cotizacion
set STREAMLIT_SERVER_ENABLECORS=false
set STREAMLIT_SERVER_TRUSTXFORWARDEDPROTO=true
set STREAMLIT_SERVER_TRUSTXFORWARDEDHOST=true
set STREAMLIT_SERVER_TRUSTXFORWARDEDPORT=true
set STREAMLIT_CLIENT_SHOWERRORDETAILS=true
set STREAMLIT_LOGGER_LEVEL=debug

REM Ruta del proyecto
cd /d "C:\Users\TEMPORAL\Documents\Automation\bot-rdnc"

REM Activar venv
call .venv\Scripts\activate.bat

REM Ejecutar Streamlit
python -m streamlit run main.py --logger.level=debug

REM Si falla, mostrar error
if errorlevel 1 (
    echo.
    echo ERROR: Streamlit no pudo iniciarse.
    echo Verifique:
    echo - Python instalado en el venv
    echo - Puerto 8501 disponible
    echo - Permisos de carpeta
    pause
)

endlocal
