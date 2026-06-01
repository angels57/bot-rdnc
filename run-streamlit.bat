
@echo off


call venv\Scripts\activate

uv run streamlit run .\main.py ^ --server.port 8501 ^ --server.address 127.0.0.1 ^ --server.baseUrlPath cotizacion ^ --browser.serverAddress www.impocoma.com.co ^ --browser.serverPort 8084 ^ --server.enableCORS false ^ --server.enableXsrfProtection false ^ --server.enableWebsocketCompression false

pause
