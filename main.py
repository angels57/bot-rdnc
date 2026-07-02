"""Módulo principal para ejecutar el bot de scrapping de RDNC y SICETAC."""

import asyncio
import os
from datetime import date, datetime

import streamlit as st

from app.core.logging import get_app_logger
from app.scrapper import playwright_rndc
from app.UI.chat_page import render
from app.UI.login_page import render_login

logger = get_app_logger("main")
DATA_FILE = "data/RNDC.xlsx"


def archivo_es_del_mes_actual(path: str) -> bool:
    if not os.path.exists(path):
        return False
    mod_time = datetime.fromtimestamp(os.path.getmtime(path))
    return mod_time.year == date.today().year and mod_time.month == date.today().month


def main():
    if not st.session_state.get("autenticado", False):
        render_login()
        return

    with st.sidebar:
        st.divider()
        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

    render()

    # if date.today().day == 1 and not archivo_es_del_mes_actual(DATA_FILE):
    #    try:
    #        asyncio.run(playwright_rndc())
    #    except Exception as e:
    #        logger.error(f"Error ejecutando playwright_rndc: {e!s}")


if __name__ == "__main__":
    main()
