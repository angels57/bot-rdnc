"""Página de login con gate de autenticación."""

import streamlit as st

from app.services.auth_service import autenticar, create_token


def render_login(cookie_manager=None):
    """Muestra el formulario de login."""
    st.title("🔐 Iniciar sesión")

    with st.form("login_form"):
        nick = st.text_input("Usuario", placeholder="Ingrese su usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", type="primary")

        if submitted:
            if not nick or not password:
                st.error("⚠️ Ingrese usuario y contraseña.")
                return

            usuario = autenticar(nick, password)
            if usuario:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                st.session_state.rol = usuario["role"]

                if "force_login" in st.session_state:
                    del st.session_state.force_login

                if cookie_manager:
                    token = create_token(usuario["nick"], usuario["role"])
                    cookie_manager.set("session_token", token)

                st.success(f"✅ Bienvenido, {usuario['nombres']}!")
            else:
                st.error("❌ Usuario o contraseña no válidos.")

    st.caption("Acceso restringido. Solo roles autorizados.")
