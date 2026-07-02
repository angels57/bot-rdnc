"""Módulo principal para ejecutar el bot de scrapping de RDNC y SICETAC."""

import extra_streamlit_components as stx
import streamlit as st

from app.services.auth_service import verify_token
from app.UI.chat_page import render as render_cotizacion
from app.UI.formulario_page import render as render_registro
from app.UI.login_page import render_login


def main():
    st.set_page_config(
        page_title="Bot RNDC",
        page_icon="🚛",
        initial_sidebar_state="expanded",
    )

    # Fast path: ya autenticado en session_state
    if st.session_state.get("autenticado"):
        _show_nav_and_content()
        return

    # No autenticado → verificar cookie (caso F5)
    cookie_manager = stx.CookieManager(key="auth_cookies")
    all_cookies = cookie_manager.get_all()

    if "cookies_loaded" not in st.session_state:
        st.session_state.cookies_loaded = True
        st.info("Cargando sesión...")
        return

    token = all_cookies.get("session_token")
    if token:
        payload = verify_token(token)
        if payload:
            # Cookie válida → restaurar sesión
            st.session_state.autenticado = True
            st.session_state.usuario = {
                "nick": payload["nick"],
                "nombres": "",
                "apellidos": "",
                "role": payload["role"],
            }
            st.session_state.rol = payload["role"]
            st.rerun()
            return
        else:
            # Token inválido/expirado → borrar cookie
            cookie_manager.delete("session_token")

    # Sin cookie válida → mostrar login
    render_login(cookie_manager)


def _show_nav_and_content():
    """Muestra navegación + contenido según vista seleccionada."""
    with st.sidebar:
        vista = st.radio(
            "Navegación",
            ["🚛 Cotización", "📝 Registro"],
            key="vista_actual",
        )
        st.divider()
        if st.button("🚪 Cerrar sesión"):
            cookie_manager = stx.CookieManager(key="auth_logout")
            cookie_manager.delete("session_token")
            st.session_state.clear()
            st.rerun()

    if vista == "🚛 Cotización":
        render_cotizacion()
    elif vista == "📝 Registro":
        render_registro()


if __name__ == "__main__":
    main()
