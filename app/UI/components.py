import streamlit as st


def render_result(resultado: dict | None):
    """Renderiza el dataframe de resultados del bot."""
    ruta_db = resultado["ruta_db"]
    ruta_sql = resultado.get("ruta_sql")

    if (ruta_db is None or ruta_db.is_empty()) and (
        ruta_sql is None or ruta_sql.is_empty()
    ):
        msg = (
            "No encontre resultados exactos para esa ruta en RDNC ni en SQL Server. "
            "Probablemente no haya datos suficientes para esa combinación de origen, destino y configuración de vehículo. "
        )
        if resultado["costo_sicetac"]:
            sicetac = f"- 🧾 Costo SICETAC: `{resultado['costo_sicetac']}`"
            msg += sicetac
        else:
            msg += "No se pudo obtener el costo de SICETAC para esta ruta."

        st.markdown(msg)
        return None, msg

    sicetac = resultado["costo_sicetac"]
    lineas = [
        f"### 🚛 Resultados para {resultado['origen']} - {resultado['destino']}\n"
    ]

    if ruta_db is not None and not ruta_db.is_empty():
        tipo_vehiculo = ruta_db["COD_CONFIG_VEHICULO"][0]
        total_viajes = ruta_db["VIAJESTOTALES"].sum()
        costo_promedio_unitario = ruta_db["VALOR_PROMEDIO_UNITARIO"].mean()

        lineas.append(
            f"**📊 Datos desde RDNC local**  \n"
            f"- 🚚 Vehículo: `{tipo_vehiculo}`  \n"
            f"- 📦 Viajes totales: `{total_viajes:,.0f}`  \n"
            f"- 💰 Flete promedio: `${costo_promedio_unitario:,.0f}`  \n"
        )
    else:
        lineas.append(
            "**📊 No se encontraron datos en RDNC local para esta combinación.**  \n"
        )

    if ruta_sql is not None and not ruta_sql.is_empty():
        fila_sql = ruta_sql.row(0)
        lineas.append("**🗄️ Datos desde SQL Server**  \n")
        lineas.append(
            f"- 📅 Fecha: `{fila_sql['Fecha_Crea']}`  \n"
            f"- 🧾 Documento: `{fila_sql['ENPD_Numero_Documento']}`  \n"
            f"- 🌍 Origen/Destino: `{fila_sql['ORIGEN']} → {fila_sql['DESTINO']}`  \n"
            f"- 🚚 Vehículo: `{fila_sql['VEHICULO']}`  \n"
            f"- 🧱 Semirremolque: `{fila_sql['SEMIRREMOLQUE']}`  \n"
            f"- 🧩 Configuración: `{fila_sql['CONFIGURACION']}`  \n"
            f"- 💵 Flete cliente: `{fila_sql['Valor_Flete_Cliente']}`"
        )
    else:
        lineas.append(
            "**🗄️ No se encontraron datos en SQL Server para esta combinación.**  \n"
        )

    lineas.append(f"- 🧾 Costo SICETAC: `{sicetac}`")
    texto = "\n".join(lineas)
    st.markdown(texto)
    return texto
