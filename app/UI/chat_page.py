"Módulo de la interfaz de chat para cotización de rutas RNDC utilizando Streamlit."

import json

import streamlit as st

from app.bot.handler import BotHandler
from app.core import get_app_logger
from app.data.loader import load_sicetac_ciudades
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

    origenes, destinos = load_sicetac_ciudades()

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
            """
        )

    col1, col2, col3 = st.columns([3, 5, 5])
    with col1:
        configuracion = st.selectbox(
            "COD vehiculo",
            [f"{c['id']} - {c['valor']}" for c in CONFIGURACIONES_VEHICULO],
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

    if "loading" not in st.session_state:
        st.session_state.loading = False

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
    if "resultado" in st.session_state and st.session_state.resultado:
        components.render_result(st.session_state.resultado)
