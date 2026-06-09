import streamlit as st

from app.core.logging import get_app_logger

logger = get_app_logger("components")


def render_result(resultado: dict | None):
    """Renderiza el dataframe de resultados del bot."""
    ruta_db = resultado["ruta_db"]
    ruta_sql = resultado.get("ruta_sql")
    logger.info(ruta_sql)

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
        fila_sql = ruta_sql

        fecha = fila_sql["FECHA"][0].strftime("%Y-%m-%d %H:%M:%S")
        origen = fila_sql["ORIGEN"][0]
        destino = fila_sql["DESTINO"][0]
        configuracion = fila_sql["CONFIGURACION"][0]
        flete_transportador = fila_sql["Valor_Flete_Transportador"][0]

        lineas.append("**🗄️ Datos desde SQL Server**  \n")
        lineas.append(
            ""
            f"- 📅 Fecha: `{fecha}`  \n"
            f"- 🌍 Origen/Destino: `{origen} → {destino}`  \n"
            f"- 🧩 Configuración: `{configuracion}`  \n"
            f"- 💵 Flete transportador: `${flete_transportador:,.1f}` \n"
        )
    else:
        lineas.append(
            "**🗄️ No se encontraron datos en SQL Server para esta combinación.**  \n"
        )

    lineas.append(f"**🧾 Costo SICETAC**: `{sicetac}`")
    texto = "\n".join(lineas)
    st.markdown(texto)
    return texto
