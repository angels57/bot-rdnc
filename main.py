"""Módulo principal para ejecutar el bot de scrapping de RDNC y SICETAC."""

import streamlit as st

from app.UI.chat_page import render as render_cotizacion
from app.UI.formulario_page import render as render_registro
from app.UI.login_page import render_login


def main():
    st.set_page_config(
        page_title="Bot RNDC",
        page_icon="🚛",
        initial_sidebar_state="expanded",
    )

    # Gate de autenticación centralizado
    if not st.session_state.get("autenticado", False):
        render_login()
        return

    # Navegación + logout en sidebar
    with st.sidebar:
        vista = st.radio(
            "Navegación",
            ["🚛 Cotización", "📝 Registro"],
            key="vista_actual",
        )
        st.divider()
        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

    # Render condicional
    if vista == "🚛 Cotización":
        render_cotizacion()
    elif vista == "📝 Registro":
        render_registro()


if __name__ == "__main__":
    main()
