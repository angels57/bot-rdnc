"""Página de gestión de usuarios."""

import streamlit as st

from app.db.crud import (
    actualizar_usuario,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
    resetear_password,
)
from app.UI.formulario_page import AGENCIAS


# Filtrar "TODOS" — no aplica para usuarios
AGENCIAS_USUARIO = [a for a in AGENCIAS if a != "TODOS"]


def render():
    """Renderiza la página de gestión de usuarios con tabs."""
    st.title("👥 Gestión de Usuarios")

    tab_crear, tab_listar = st.tabs(["➕ Crear", "📋 Listar / Editar"])

    # --- Tab Crear ---
    with tab_crear:
        with st.form("crear_usuario_form"):
            nombres = st.text_input("Nombres", placeholder="ej: Juan")
            apellidos = st.text_input("Apellidos", placeholder="ej: Doe")
            role = st.selectbox(
                "Rol", ["ADMIN", "FLETES", "COMERCIAL"], key="crear_role"
            )
            agencia = st.selectbox("Agencia", AGENCIAS_USUARIO, key="crear_agencia")
            submitted = st.form_submit_button("Crear usuario", type="primary")

            if submitted:
                if not nombres or not apellidos:
                    st.error("⚠️ Todos los campos son obligatorios.")
                else:
                    resultado = crear_usuario(nombres, apellidos, role, agencia)
                    if resultado:
                        st.success("✅ Usuario creado correctamente.")
                        st.code(
                            f"Link: https://www.impocoma.com.co:8084/cotizacion\n"
                            f"Usuario: {resultado['nick']}\n"
                            f"Contraseña: {resultado['password']}",
                            language="text",
                        )
                        st.caption(
                            "🔒 Copia estos datos con el botón 📋 y compártelos de forma segura. No se volverán a mostrar."
                        )
                    else:
                        st.error("❌ No se pudo crear el usuario.")
        st.caption("El usuario y la contraseña se generan automáticamente.")

    # --- Tab Listar / Editar ---
    with tab_listar:
        usuarios = listar_usuarios()
        if not usuarios:
            st.info("No hay usuarios registrados.")
            return

        for u in usuarios:
            fecha_creacion = (
                u.fecha_creacion.strftime("%Y-%m-%d") if u.fecha_creacion else "N/A"
            )
            ultima = (
                u.ultima_conexion.strftime("%Y-%m-%d %H:%M")
                if u.ultima_conexion
                else "Nunca"
            )
            agencia = u.usr_agencia or "N/A"
            with st.expander(
                f"👤 {u.usr_nick} — {u.usr_nombres} {u.usr_apellidos} ({u.usr_role}) | 🏢 {agencia} | 📅 {fecha_creacion} | 🕒 {ultima}"
            ):
                col_edit, col_reset, col_del = st.columns([3, 1, 1])

                with col_edit:
                    with st.form(f"editar_{u.usr_nick}"):
                        nuevos_nombres = st.text_input(
                            "Nombres", value=u.usr_nombres, key=f"nombres_{u.usr_nick}"
                        )
                        nuevos_apellidos = st.text_input(
                            "Apellidos",
                            value=u.usr_apellidos,
                            key=f"apellidos_{u.usr_nick}",
                        )
                        nuevo_role = st.selectbox(
                            "Rol",
                            ["ADMIN", "FLETES", "COMERCIAL"],
                            index=["ADMIN", "FLETES", "COMERCIAL"].index(u.usr_role),
                            key=f"role_{u.usr_nick}",
                        )
                        agencia_actual = (
                            u.usr_agencia
                            if u.usr_agencia in AGENCIAS_USUARIO
                            else AGENCIAS_USUARIO[0]
                        )
                        nueva_agencia = st.selectbox(
                            "Agencia",
                            AGENCIAS_USUARIO,
                            index=AGENCIAS_USUARIO.index(agencia_actual)
                            if agencia_actual in AGENCIAS_USUARIO
                            else 0,
                            key=f"agencia_{u.usr_nick}",
                        )
                        if st.form_submit_button("💾 Guardar cambios"):
                            ok = actualizar_usuario(
                                u.usr_nick,
                                nuevos_nombres,
                                nuevos_apellidos,
                                nuevo_role,
                                nueva_agencia,
                            )
                            if ok:
                                st.success("✅ Cambios guardados.")
                                st.rerun()
                            else:
                                st.error("❌ No se pudo actualizar.")

                with col_reset:
                    if st.button("🔑 Resetear contraseña", key=f"reset_{u.usr_nick}"):
                        new_pass = resetear_password(u.usr_nick)
                        if new_pass:
                            st.success("✅ Contraseña reseteada correctamente.")
                            st.code(
                                f"Link: https://www.impocoma.com.co:8084/cotizacion\n"
                                f"Usuario: {u.usr_nick}\n"
                                f"Contraseña: {new_pass}",
                                language="text",
                            )
                            st.caption(
                                "🔒 Copia estos datos con el botón 📋 y compártelos de forma segura. No se volverán a mostrar."
                            )
                        else:
                            st.error("❌ No se pudo resetear.")

                with col_del:
                    if st.button("🗑️ Eliminar", key=f"del_{u.usr_nick}"):
                        # No eliminar el propio admin logueado
                        if u.usr_nick == st.session_state.get("usuario", {}).get(
                            "nick"
                        ):
                            st.error("❌ No puedes eliminar tu propio usuario.")
                        else:
                            ok = eliminar_usuario(u.usr_nick)
                            if ok:
                                st.success(f"✅ Usuario '{u.usr_nick}' eliminado.")
                                st.rerun()
                            else:
                                st.error("❌ No se pudo eliminar.")
