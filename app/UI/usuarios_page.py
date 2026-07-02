"""Página de creación rápida de usuarios."""

import streamlit as st

from app.db.crud import crear_usuario


def render():
    """Renderiza el formulario de creación de usuarios."""
    st.title("👥 Crear Usuario")

    with st.form("crear_usuario_form"):
        nombres = st.text_input("Nombres", placeholder="ej: Juan")
        apellidos = st.text_input("Apellidos", placeholder="ej: Doe")
        role = st.selectbox("Rol", ["ADMIN", "FLETES", "COMERCIAL"])
        submitted = st.form_submit_button("Crear usuario", type="primary")

        if submitted:
            if not nombres or not apellidos:
                st.error("⚠️ Todos los campos son obligatorios.")
                return

            resultado = crear_usuario(nombres, apellidos, role)
            if resultado:
                st.success("✅ Usuario creado correctamente.")
                st.info(f"👤 Usuario: `{resultado['nick']}`")
                st.info(f"🔑 Contraseña: `{resultado['password']}`")
                st.caption("Copia estos datos y compártelos con el usuario. No se volverán a mostrar.")
            else:
                st.error("❌ No se pudo crear el usuario.")

    st.caption("El usuario y la contraseña se generan automáticamente.")
