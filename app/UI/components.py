import streamlit as st

from app.core.logging import get_app_logger

logger = get_app_logger("components")


def render_result(resultado: dict | None):
    """Renderiza el dataframe de resultados del bot con tarjetas visuales."""
    ruta_db = resultado["ruta_db"]
    ruta_sql = resultado.get("ruta_sql")
    logger.info(ruta_sql)

    # Encabezado
    st.markdown(
        f"### 🚛 Resultados para {resultado['origen']} - {resultado['destino']}"
    )

    # Caso sin datos en ninguna fuente
    if (ruta_db is None or ruta_db.is_empty()) and (
        ruta_sql is None or ruta_sql.is_empty()
    ):
        with st.container(border=True):
            col_icon, col_msg = st.columns([1, 5])
            with col_icon:
                st.markdown("# ⚠️")
            with col_msg:
                st.markdown("#### No se encontraron resultados")
                st.markdown(
                    "No hay datos en **RDNC** ni en **TMS** para esta combinación "
                    "de origen, destino y configuración de vehículo."
                )
                if resultado["costo_sicetac"]:
                    st.metric(
                        "🧾 Costo SICETAC disponible",
                        f"${resultado['costo_sicetac']}",
                    )
                    if resultado.get("costo_tonelada"):
                        st.metric(
                            "💰 Costo por ton   elada",
                            f"${resultado['costo_tonelada']}",
                        )
                else:
                    st.warning("No se pudo obtener costo SICETAC para esta ruta.")
        return None

    # Dos columnas: RDNC | TMS
    col_db, col_sql = st.columns(2)

    with col_db, st.container(border=True):
        st.markdown("#### 📊 RDNC local")
        if ruta_db is not None and not ruta_db.is_empty():
            tipo_vehiculo = ruta_db["COD_CONFIG_VEHICULO"][0]
            total_viajes = ruta_db["VIAJESTOTALES"].sum()
            costo_promedio_unitario = ruta_db["VALOR_PROMEDIO_UNITARIO"].mean()

            st.markdown(f"🚚 **{tipo_vehiculo}**")
            st.metric("Viajes totales", f"{total_viajes:,.0f}")
            st.metric("Flete promedio", f"${costo_promedio_unitario:,.0f}")
        else:
            st.markdown("⛔ **Sin datos**")
            st.caption("No hay registros para esta combinación en RDNC.")

    with col_sql, st.container(border=True):
        st.markdown("#### 🗄️ TMS (SQL Server)")
        if ruta_sql is not None and not ruta_sql.is_empty():
            fila_sql = ruta_sql
            fecha = fila_sql["FECHA"][0].strftime("%Y-%m-%d %H:%M:%S")
            configuracion = fila_sql["CONFIGURACION"][0]
            flete_transportador = fila_sql["Valor_Flete_Transportador"][0]

            st.metric("Flete transportador", f"${flete_transportador:,.1f}")
            st.caption(f"Fecha: {fecha} | Config: {configuracion}")
        else:
            st.markdown("⛔ **Sin datos**")
            st.caption("No hay registros para esta combinación en TMS.")

    # SICETAC — tarjeta inferior
    with st.container(border=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if resultado["costo_sicetac"]:
                st.metric("🧾 Costo SICETAC (total)", f"${resultado['costo_sicetac']}")
            else:
                st.warning("No se pudo obtener costo SICETAC")
        with col_c2:
            if resultado.get("costo_tonelada"):
                st.metric("💰 Costo por tonelada", f"${resultado['costo_tonelada']}")

    # Registros previos — tarjeta de fletes registrados
    fletes_registrados = resultado.get("fletes_registrados", [])
    if fletes_registrados:
        with st.container(border=True):
            st.markdown("#### 📝 Registros previos")
            for registro in fletes_registrados[:5]:
                col_f1, col_f2 = st.columns([3, 2])
                with col_f1:
                    tarifa = registro.get("tarifa", 0)
                    tipo_flete = registro.get("tipo_flete", "N/A")
                    st.write(f"**${tarifa:,.0f}** ({tipo_flete})")
                with col_f2:
                    fuente = registro.get("fuente", "N/A")
                    agencia = registro.get("agencia", "N/A")
                    creado = registro.get("creado_en", "")
                    fecha_corta = creado[:10] if creado else ""
                    st.caption(f"{fuente} · {agencia} · {fecha_corta}")
    else:
        with st.container(border=True):
            st.markdown("#### 📝 Registros previos")
            st.markdown("⛔ **Sin registros**")
            st.caption("No hay fletes registrados para esta combinación.")

    return None
