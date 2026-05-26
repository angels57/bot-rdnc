import streamlit as st


def render_result(resultado: dict | None):
    """Renderiza los resultados del bot utilizando un diseño híbrido y moderno en columnas."""
    if not resultado:
        return

    origen = resultado.get("origen", "Origen")
    destino = resultado.get("destino", "Destino")
    df_group = resultado.get("ruta_db")
    sicetac = resultado.get("costo_sicetac")

    # Verificamos si ambas fuentes están vacías
    rndc_vacio = df_group is None or df_group.is_empty()
    sicetac_vacio = not sicetac

    if rndc_vacio and sicetac_vacio:
        st.error(
            "⚠️ No se encontraron resultados en ninguna de las fuentes de datos (RNDC / SICETAC) "
            "para la combinación seleccionada."
        )
        return

    # Título principal con diseño elegante
    st.markdown(f"### 🚛 Resultados de Cotización: **{origen}** → **{destino}**")

    # Si RNDC tiene datos, extraemos la configuración del vehículo
    tipo_vehiculo = ""
    if df_group is not None and not df_group.is_empty():
        tipo_vehiculo = df_group["COD_CONFIG_VEHICULO"][0]
        st.info(f"🚚 **Vehículo Detectado:** {tipo_vehiculo}")

    # Layout de 2 columnas para presentación híbrida
    col_rndc, col_sicetac = st.columns(2)

    # --- COLUMNA 1: HISTÓRICO RNDC ---
    with col_rndc:
        st.markdown("#### 📊 Historial Operativo RNDC")
        if df_group is not None and not df_group.is_empty():
            total_viajes = df_group["VIAJESTOTALES"].sum()
            costo_promedio = df_group["VALOR_PROMEDIO_UNITARIO"].mean()

            # Creamos una sub-distribución para las métricas
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                st.metric(
                    label="📦 Viajes Totales",
                    value=f"{total_viajes:,.0f}",
                    help="Número total de viajes registrados en RNDC",
                )
            with sub_col2:
                # Si SICETAC también tiene valor, podemos calcular un delta/comparativa inteligente
                delta_val = None
                if isinstance(sicetac, int | float) and costo_promedio:
                    diferencia = costo_promedio - sicetac
                    porcentaje = (diferencia / sicetac) * 100
                    delta_val = f"{porcentaje:+.1f}% vs SICETAC"

                st.metric(
                    label="💰 Flete Promedio",
                    value=f"${costo_promedio:,.0f}",
                    delta=delta_val,
                    delta_color="inverse" if delta_val else "normal",
                )
        else:
            st.warning(
                "No hay suficientes registros históricos en la base de datos RNDC "
                "para esta combinación de origen, destino y tipo de vehículo."
            )

    # --- COLUMNA 2: REFERENCIA OFICIAL SICETAC ---
    with col_sicetac:
        st.markdown("#### 🧾 Costo de Referencia SICETAC")
        if not sicetac_vacio:
            # Limpiamos y formateamos el valor de SICETAC
            if isinstance(sicetac, int | float):
                sicetac_display = f"${sicetac:,.0f}"
            else:
                # Si viene como string formateado
                sicetac_display = str(sicetac)

            st.metric(
                label="💵 Tarifa Calculada",
                value=sicetac_display,
                help="Costo oficial de referencia de SICETAC",
            )
        else:
            st.warning(
                "No se pudo calcular el costo de referencia en SICETAC. "
                "Verifique si la ruta y configuración del vehículo están registradas."
            )
