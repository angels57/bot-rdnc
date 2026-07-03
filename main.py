"""Módulo principal para ejecutar el bot de scrapping de RDNC y SICETAC."""

import extra_streamlit_components as stx
import streamlit as st

from app.services.auth_service import verify_token
from app.db.crud import get_usuario
from app.UI.chat_page import render as render_cotizacion
from app.UI.formulario_page import render as render_registro
from app.UI.login_page import render_login
from app.UI.masivo_page import render as render_masivo
from app.UI.usuarios_page import render as render_usuarios
from app.UI.reporte_page import render as render_reporte


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

    if st.session_state.get("force_login"):
        render_login(cookie_manager)
        return

    token = all_cookies.get("session_token")
    if token:
        payload = verify_token(token)
        if payload:
            # Cookie válida → restaurar sesión
            st.session_state.autenticado = True
            # Intentar cargar datos completos del usuario desde DB
            usuario_db = get_usuario(payload["nick"]) if payload.get("nick") else None
            if usuario_db:
                st.session_state.usuario = usuario_db
                st.session_state.rol = usuario_db.get("role")
            else:
                st.session_state.usuario = {
                    "nick": payload["nick"],
                    "nombres": "",
                    "apellidos": "",
                    "role": payload["role"],
                    "agencia": None,
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
        # Mostrar información del usuario en la parte superior izquierda
        usuario = st.session_state.get("usuario", {})
        nombre_completo = f"{usuario.get('nombres', '').strip()} {usuario.get('apellidos', '').strip()}".strip()
        if not nombre_completo:
            nombre_completo = usuario.get("nick", "")
        agencia = usuario.get("agencia") or "N/A"
        role_text = usuario.get("role", "")

        if nombre_completo or role_text or agencia:
            st.markdown(f"**{nombre_completo}**")
            st.markdown(f"**Rol:** {role_text}  |  **Agencia:** {agencia}")
            st.divider()

        rol = st.session_state.get("rol", "")
        opciones = []
        if rol in ("ADMIN", "COMERCIAL"):
            opciones.append("🚛 Cotización Comercial")
            opciones.append("📊 Cotización Comercial Masivo")
            opciones.append("📈 Reporte")
        if rol in ("ADMIN", "FLETES"):
            opciones.append("📝 Registro Fletes Plaza")
        if rol == "ADMIN":
            opciones.append("👥 Administrar Usuarios")

        vista = st.radio("Navegación", opciones, key="vista_actual")
        st.divider()
        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.session_state["force_login"] = True
            cookie_manager = stx.CookieManager(key="auth_logout")
            try:
                cookie_manager.delete("session_token")
            except KeyError:
                pass
            st.stop()

    if vista == "🚛 Cotización Comercial":
        render_cotizacion()
    elif vista == "📊 Cotización Comercial Masivo":
        render_masivo()
    elif vista == "📝 Registro Fletes Plaza":
        render_registro()
    elif vista == "👥 Administrar Usuarios":
        render_usuarios()
    elif vista == "📈 Reporte":
        render_reporte()


if __name__ == "__main__":
    main()
