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
        st.markdown("#### 🧾 SICETAC")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if resultado["costo_sicetac"]:
                try:
                    valor = float(resultado["costo_sicetac"])
                    st.metric("Costo total del viaje", f"${valor:,.0f}")
                except (ValueError, TypeError):
                    st.metric("Costo total del viaje", resultado["costo_sicetac"])
            else:
                st.metric("Costo total del viaje", "—")
                st.caption("⛔ Sin datos")
        with col_c2:
            if resultado.get("costo_tonelada"):
                try:
                    valor = float(resultado["costo_tonelada"])
                    st.metric("Costo por tonelada", f"${valor:,.0f}")
                except (ValueError, TypeError):
                    st.metric("Costo por tonelada", resultado["costo_tonelada"])
            else:
                st.metric("Costo por tonelada", "—")
                st.caption("⛔ Sin datos")

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
