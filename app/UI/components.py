import streamlit as st


def render_result(resultado: dict | None):
    """Renderiza el dataframe de resultados del bot."""
    sicetac_valor = resultado["costo_sicetac"]
    sicetac_disponible = bool(sicetac_valor) and str(sicetac_valor).strip() != ""

    if resultado["ruta_db"] is None or resultado["ruta_db"].is_empty():
        msg = "No encontre resultados exactos para esa ruta en RDNC. Probablemente no haya datos suficientes para esa combinación de origen, destino y configuración de vehículo. "
        if sicetac_disponible:
            sicetac = f"- 🧾 Costo SICETAC: `{sicetac_valor}`"
            msg += sicetac
        else:
            msg += "No se pudo obtener el costo de SICETAC para esta ruta."

        st.markdown(msg)
        return None, msg

    # Agrupar por tipo de vehiculo por polars
    # grupos = resultado.partition_by("COD_CONFIG_VEHICULO", as_dict=True)

    sicetac = sicetac_valor if sicetac_disponible else "No disponible"
    lineas = [
        f"### 🚛 Resultados para {resultado['origen']} - {resultado['destino']}\n"
    ]

    df_group = resultado["ruta_db"]

    tipo_vehiculo = df_group["COD_CONFIG_VEHICULO"][0]
    # Calcular metricas
    total_viajes = df_group["VIAJESTOTALES"].sum()
    costo_promedio_unitario = df_group["VALOR_PROMEDIO_UNITARIO"].mean()
    # diferencia_costo = costo_promedio_unitario - sicetac

    # Mostrar en 3 columnas con números formateados

    lineas.append(
        f"**🚚 {tipo_vehiculo}**  \n"
        f"- 📦 Viajes totales: `{total_viajes:,.0f}`  \n"
        f"- 💰 Flete promedio: `${costo_promedio_unitario:,.0f}`  \n"
        f"- 🧾 Costo SICETAC: `{sicetac}`"
    )
    texto = "\n".join(lineas)
    st.markdown(texto)
    return texto
