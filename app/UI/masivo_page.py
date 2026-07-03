"""Página de cotización comercial masivo vía Excel."""

import io
import os
import unicodedata

import polars as pl
import streamlit as st

from app.core import get_app_logger, sicetac_cache
from app.data.validation_rules import validar_fila
from app.models.sicetac import SicetacParams
from app.UI.chat_page import get_bot

logger = get_app_logger("masivo_page")


def _normalize_column_name(name: str) -> str:
    if name is None:
        return ""
    normalized = unicodedata.normalize("NFKD", str(name).strip().lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.replace(" ", "").replace("-", "_")
    normalized = normalized.replace(".", "")
    return normalized


def _validate_excel_columns(df: pl.DataFrame) -> tuple[bool, dict[str, str], str]:
    normalized_to_original = {_normalize_column_name(name): name for name in df.columns}
    expected_columns = {
        "origen": ["origen", "origen"],
        "destino": ["destino", "destino"],
        "configuracion": [
            "configuracion",
            "configuracionvehiculo",
            "codvehiculo",
            "codconfiguracion",
            "codconfig",
        ],
        "condicion_carga": [
            "condicioncarga",
            "condicion_carga",
            "condiciondecarga",
        ],
        "carroceria": ["carroceria", "carrocería"],
        "tipo_carga": ["tipocarga", "tipo_carga", "tipodecarga"],
        "horas_cargue_descargue": [
            "horascarguedescargue",
            "horas_cargue_descargue",
            "horascargue_descargue",
            "horasdecarguedescargue",
        ],
    }

    columns_map: dict[str, str] = {}
    missing: list[str] = []
    for canonical, possibilities in expected_columns.items():
        match = next(
            (
                normalized_to_original.get(_normalize_column_name(pos))
                for pos in possibilities
                if _normalize_column_name(pos) in normalized_to_original
            ),
            None,
        )
        if match is None:
            missing.append(canonical)
        else:
            columns_map[canonical] = match

    if missing:
        actual_columns = ", ".join(str(name) for name in df.columns)
        expected_list = ", ".join(expected_columns.keys())
        return (
            False,
            {},
            f"El archivo debe contener las columnas: {expected_list}. Columnas faltantes: {', '.join(missing)}. Columnas detectadas: {actual_columns}",
        )

    return True, columns_map, ""


def _to_excel_bytes(df: pl.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_pandas().to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.read()


def generar_template_excel_bytes() -> bytes:
    df = pl.DataFrame(
        {
            "origen": [""],
            "destino": [""],
            "configuracion": [""],
            "condicion_carga": [""],
            "carroceria": [""],
            "tipo_carga": [""],
            "horas_cargue_descargue": [""],
        }
    )
    return _to_excel_bytes(df)


def obtener_template_existente_bytes() -> tuple[bytes, bool]:
    template_path = "data/Format_sicetac_automatizacion.xlsx"
    if os.path.exists(template_path):
        try:
            with open(template_path, "rb") as f:
                return f.read(), True
        except Exception as e:
            logger.warning(
                f"No se pudo leer la plantilla existente '{template_path}': {e!s}"
            )

    return generar_template_excel_bytes(), False


def refrescar_cache() -> None:
    try:
        sicetac_cache.clear()
        st.success("Caché de rutas SICETAC refrescado correctamente.")
    except Exception as e:
        st.error(f"No se pudo refrescar el caché: {e!s}")
        logger.error(f"Error al refrescar caché: {e!s}")


def procesar_archivo_excel(file, bot) -> pl.DataFrame | None:
    try:
        contenido = file.read()
        df = pl.read_excel(io.BytesIO(contenido))
    except Exception as e:
        st.error(f"No se pudo leer el archivo Excel: {e!s}")
        logger.error(f"Error leyendo Excel: {e!s}")
        return None

    if df.is_empty():
        st.warning("El archivo Excel no contiene filas para procesar.")
        return None

    valid, columns_map, error_message = _validate_excel_columns(df)
    if not valid:
        st.error(error_message)
        return None

    filas_procesadas = []
    filas_con_error = 0
    filas_procesadas_exitosamente = 0

    with st.spinner("Validando y procesando rutas desde Excel..."):
        for row in df.iter_rows(named=True):
            es_valida, errores = validar_fila(row, columns_map)

            fila = dict(row)

            if not es_valida:
                fila["observacion"] = "; ".join(errores)
                fila["costo_sicetac"] = ""
                fila["costo_tonelada"] = ""
                filas_con_error += 1
            else:
                try:
                    params = SicetacParams(
                        origen=str(row[columns_map["origen"]]).strip(),
                        destino=str(row[columns_map["destino"]]).strip(),
                        configuracion=str(row[columns_map["configuracion"]]).strip(),
                        condicion_carga=str(
                            row[columns_map["condicion_carga"]]
                        ).strip(),
                        carroceria=str(row[columns_map["carroceria"]]).strip(),
                        tipo_carga=str(row[columns_map["tipo_carga"]]).strip(),
                        horas_cargue_descargue=str(
                            row[columns_map["horas_cargue_descargue"]]
                        ).strip(),
                    )
                    costo = bot._run_scrapping(params)
                    if isinstance(costo, dict):
                        fila["costo_sicetac"] = costo.get("costo_total", "")
                        fila["costo_tonelada"] = costo.get("costo_tonelada", "")
                    elif costo:
                        fila["costo_sicetac"] = costo
                        fila["costo_tonelada"] = ""
                    else:
                        fila["costo_sicetac"] = ""
                        fila["costo_tonelada"] = ""
                    fila["observacion"] = ""
                    filas_procesadas_exitosamente += 1
                except Exception as e:
                    fila["observacion"] = f"Error al procesar: {e!s}"
                    fila["costo_sicetac"] = ""
                    fila["costo_tonelada"] = ""
                    filas_con_error += 1
                    logger.error(f"Error procesando fila: {e!s}")

            filas_procesadas.append(fila)

    st.info(
        f"✅ Filas procesadas: {filas_procesadas_exitosamente} | ⚠️ Filas con errores: {filas_con_error}"
    )

    return pl.from_dicts(filas_procesadas)


def procesar_excel(file):
    if not file:
        st.warning("Sube un archivo Excel con las rutas antes de procesar.")
        return

    st.session_state.loading = True
    try:
        bot = get_bot()
        resultado_excel = procesar_archivo_excel(file, bot)
        if resultado_excel is not None:
            st.session_state.excel_result = resultado_excel
            st.success("Archivo procesado correctamente.")
    except Exception as e:
        st.error(f"Error procesando el archivo Excel: {e!s}")
        logger.error(f"Error procesando archivo Excel: {e!s}")
    finally:
        st.session_state.loading = False


def render():
    """Renderiza la página de carga masiva de Excel."""
    st.title("📊 Cotización Comercial Masivo")

    if "loading" not in st.session_state:
        st.session_state.loading = False

    with st.expander("❓ Instrucciones de uso"):
        st.write(
            """
            1. Descarga la **plantilla Excel**.
            2. Completa los datos de las rutas (origen, destino, configuración, etc.).
            3. Sube el archivo Excel completado.
            4. Haz clic en **Procesar archivo Excel**.
            5. Descarga los resultados con los costos de SICETAC.
            """
        )

    template_bytes, existe_template = obtener_template_existente_bytes()
    file_name = (
        "Format_sicetac_automatizacion.xlsx"
        if existe_template
        else "template_sicetac.xlsx"
    )

    # Card 1: Plantilla
    with st.container(border=True):
        st.markdown("### 📥 Plantilla")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Descargar plantilla Excel",
                data=template_bytes,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.button(
                "Refrescar caché SICETAC",
                on_click=refrescar_cache,
                disabled=st.session_state.loading,
                use_container_width=True,
            )
        st.caption("Descarga la plantilla, completa los datos y súbela para procesar.")

    # Card 2: Cargar archivo
    with st.container(border=True):
        st.markdown("### 📤 Cargar archivo")
        excel_file = st.file_uploader(
            "Sube un archivo Excel con las rutas a procesar",
            type=["xlsx", "xls"],
            key="excel_file",
        )
        if excel_file:
            st.button(
                "Procesar archivo Excel",
                on_click=procesar_excel,
                args=(excel_file,),
                disabled=st.session_state.loading,
                type="primary",
            )

    # Card 3: Resultados
    if "excel_result" in st.session_state and st.session_state.excel_result is not None:
        with st.container(border=True):
            st.markdown("### 📊 Resultados")
            st.dataframe(st.session_state.excel_result.to_pandas())
            excel_bytes = _to_excel_bytes(st.session_state.excel_result)
            st.download_button(
                "Descargar Excel con costo SICETAC",
                data=excel_bytes,
                file_name="resultado_sicetac.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
