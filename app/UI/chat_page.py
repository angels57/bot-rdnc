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
            """
        )

    configuracion = st.selectbox(
        "COD vehiculo",
        [c["id"] for c in CONFIGURACIONES_VEHICULO],
        format_func=lambda cod: (
            f"{cod} — {next((c['valor'] for c in CONFIGURACIONES_VEHICULO if c['id'] == cod), '')}"
        ),
    )

    col1, col2, col3 = st.columns([3, 5, 5])
    with col1:
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

    # Calculadora de comisión independiente
    with st.expander("💰 Calcular valor + comisión"):
        valor_base = st.number_input(
            "Valor base",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.2f",
            key="valor_base_comision",
        )
        porcentaje_comision = st.number_input(
            "Porcentaje de comisión (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.1,
            format="%.1f",
            key="porcentaje_comision",
        )

        comision = valor_base * porcentaje_comision / 100.0
        total_con_comision = valor_base + comision

        col_comision, col_total = st.columns(2)
        with col_comision:
            st.metric("Comisión", f"${comision:,.2f}")
        with col_total:
            st.metric("Valor + comisión", f"${total_con_comision:,.2f}")

        st.caption(
            "Esta calculadora aplica una comisión sobre el valor base y muestra el total a cobrar."
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
