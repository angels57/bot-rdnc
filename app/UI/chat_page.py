"Módulo de la interfaz de chat para cotización de rutas RNDC utilizando Streamlit."

import io
import json
import os
import unicodedata

import polars as pl
import streamlit as st

from app.bot.handler import BotHandler
from app.core import get_app_logger, sicetac_cache
from app.data.loader import load_sicetac_ciudades
from app.data.validation_rules import validar_fila
from app.models.sicetac import SicetacParams
from app.UI import components, state

logger = get_app_logger("chat_page")

CONFIGURACIONES_VEHICULO = [
    {"id": "3S3", "valor": "Tractocamión tres ejes con semiremolque de tres ejes"},
    {"id": "3S2", "valor": "Tractocamión tres ejes con semiremolque de dos ejes"},
    {"id": "2S2", "valor": "Tractocamión dos ejes con semiremolque de dos ejes"},
    {"id": "2S3", "valor": "Tractocamión dos ejes con semiremolque de tres ejes"},
    {"id": "3", "valor": "Camión tres ejes"},
    {"id": "V2", "valor": "Volqueta dos ejes"},
    {"id": "V3", "valor": "Volqueta tres ejes"},
    {"id": "V4", "valor": "Volqueta cuatro ejes"},
    {"id": "2", "valor": "Camión dos ejes - PBV mas de 10500 Kg"},
    {"id": "2_7_8", "valor": "Camión dos ejes - Livianos PBV 7500-8000 Kg"},
    {"id": "2_8_9", "valor": "Camión dos ejes - Livianos PBV 8001-9000 Kg"},
    {"id": "2_9_105", "valor": "Camión dos ejes - Livianos PBV 9001-10500 Kg"},
]


@st.cache_data
def get_destinos_por_origen(origen: str) -> list[str]:
    if not origen:
        return []

    with open("data/sicetac_combinaciones.json", encoding="utf-8") as f:
        combinaciones = json.load(f)

    return combinaciones.get(origen, [])


@st.cache_resource
def get_bot() -> BotHandler:
    return BotHandler()


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


def procesar_archivo_excel(file, bot: BotHandler) -> pl.DataFrame | None:
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

    # Mostrar resumen
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


def ejecutar(
    origen,
    destino,
    configuracion,
    condicion_carga,
    carroceria,
    tipo_carga,
    horas_cargue_descargue,
):
    "Ejecuta la consulta de ruta en el bot y muestra los resultados en la interfaz."
    # Bloqueamos el botón y mostramos un spinner durante la operación
    if not origen or not destino:
        st.warning(
            "Selecciona ciudad de origen y ciudad de destino antes de consultar."
        )
        return

    bot = get_bot()

    st.session_state.loading = True
    try:
        with st.spinner("Consultando ruta, por favor espera..."):
            params = SicetacParams(
                origen=origen,
                destino=destino,
                configuracion=configuracion,
                condicion_carga=condicion_carga,
                carroceria=carroceria,
                tipo_carga=tipo_carga,
                horas_cargue_descargue=horas_cargue_descargue,  # 👈 importante
            )

            resultado = bot.run(params)

            st.session_state.resultado = resultado
    except ValueError as e:
        st.error(
            f"Error: Ciudad o municipio no encontrado - seleccione un origen y destino válidos. {e}"
        )
    except Exception as e:
        st.error(f"Error inesperado al consultar la ruta: {e!s}")
        logger.error(f"Error inesperado al consultar la ruta: {e!s}")
    finally:
        st.session_state.loading = False


def render():
    """Renderiza la interfaz de chat para cotización de rutas RNDC."""

    st.set_page_config(page_title="Bot RNDC", page_icon="🚛")
    st.title("Cotizacion de Rutas RNDC")

    state.init_state()

    if "loading" not in st.session_state:
        st.session_state.loading = False

    origenes, _ = load_sicetac_ciudades()

    with st.expander("❓ Instrucciones de uso"):
        st.write(
            """
            1. Selecciona el **origen** y **destino** de la ruta.
            2. Elige la **configuración del vehículo** que deseas cotizar.
            3. Define la **condición de carga** (CARGADO o VACIO).
            4. Selecciona el tipo de **carrocería**.
            5. Indica el **tipo de carga** (General o Granel Sólido).
            6. Especifica las **horas de cargue/descargue**.
            7. Haz clic en "Consultar ruta" para obtener la cotización.
            8. En el panel lateral puedes cargar un archivo Excel para procesar múltiples rutas.
            """
        )

    if "excel_result" in st.session_state and st.session_state.excel_result is not None:
        st.markdown("### ✅ Resultado del archivo Excel")
        st.dataframe(st.session_state.excel_result.to_pandas())
        excel_bytes = _to_excel_bytes(st.session_state.excel_result)
        st.download_button(
            "Descargar Excel con costo SICETAC",
            data=excel_bytes,
            file_name="resultado_sicetac.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with st.sidebar:
        st.header("Carga masiva Excel")

        template_bytes, existe_template = obtener_template_existente_bytes()
        file_name = (
            "Format_sicetac_automatizacion.xlsx"
            if existe_template
            else "template_sicetac.xlsx"
        )

        st.download_button(
            "Descargar plantilla Excel",
            data=template_bytes,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.button(
            "Refrescar caché SICETAC",
            on_click=refrescar_cache,
            disabled=st.session_state.loading,
        )
        st.caption("Descarga la plantilla, completa los datos, súbela y procesa.")

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
            )

    col1, col2, col3 = st.columns([3, 5, 5])
    with col1:
        configuracion = st.selectbox(
            "COD vehiculo",
            [c["id"] for c in CONFIGURACIONES_VEHICULO],
        )
        condicion_carga = st.selectbox(
            "Condición de carga",
            ["CARGADO", "VACIO"],
            key="condicion_carga",
        )
        horas_cargue_descargue = st.selectbox(
            "Horas cargue/descargue",
            ["1", "2", "3", "4", "5", "6"],
            key="horas_cargue_descargue",
        )
    with col2:
        origen = st.selectbox(
            "Ciudad de origen",
            ["", *origenes],
            key="origen",
        )
        carroceria = st.selectbox(
            "Carrocería",
            [
                "ESTACAS",
                "ESTIBAS",
                "TANQUE",
                "FURGON",
                "PORTACONTENEDORES",
                "TRAYLER",
                "VOLCO",
                "PLATAFORMA",
                "FURGON REFRIGERADO",
            ],
            key="carroceria",
        )

    destinos_disponibles = get_destinos_por_origen(origen)

    with col3:
        destino = st.selectbox(
            "Ciudad de destino",
            ["", *destinos_disponibles],
            key="destino",
        )
        tipo_carga = st.selectbox(
            "Tipo de carga",
            [
                "General",
                "Granel Sólido",
            ],
            key="tipo_carga",
        )

    # Botón fuera del handler: se deshabilita cuando `loading` es True
    st.button(
        "Consultar ruta",
        on_click=ejecutar,
        args=(
            origen,
            destino,
            configuracion,
            condicion_carga,
            carroceria,
            tipo_carga,
            horas_cargue_descargue,
        ),
        disabled=st.session_state.loading,
    )
    if "resultado" not in st.session_state:
        with st.container(border=True):
            col_icon, col_msg = st.columns([1, 5])
            with col_icon:
                st.markdown("# 👋")
            with col_msg:
                st.markdown("### Completa los parámetros y consulta una ruta")
                st.markdown(
                    "Selecciona origen, destino, configuración del vehículo y demás parámetros, "
                    "luego haz clic en **Consultar ruta** para obtener la cotización.\n\n"
                    "Los resultados incluirán:\n"
                    "- 📊 Datos históricos desde **RDNC**\n"
                    "- 🗄️ Datos desde **TMS** (SQL Server)\n"
                    "- 🧾 Costo estimado desde **SICETAC**"
                )
    elif st.session_state.resultado:
        components.render_result(st.session_state.resultado)
