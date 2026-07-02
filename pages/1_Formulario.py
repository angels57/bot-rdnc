"""Página de formulario independiente."""

import json
from pathlib import Path

import streamlit as st

from app.db.crud import guardar_flete, init_db, obtener_ultimos_registros
from app.UI.login_page import render_login

if not st.session_state.get("autenticado", False):
    render_login()
    st.stop()

with st.sidebar:
    st.divider()
    if st.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = init_db()
if not st.session_state.db_initialized:
    st.error("⚠️ No se pudo conectar a la base de datos. Contacta al administrador.")
    st.stop()

st.set_page_config(page_title="Registro de flete", page_icon="📝")
st.title("Registro de precio de flete")

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

AGENCIAS = [
    "TODOS",
    "BARRANQUILLA",
    "BOGOTA",
    "BUENAVENTURA",
    "CALI",
    "CARTAGENA",
    "CARTAGENA ITR",
    "CARTAGENA MADROÑO",
    "CUCUTA",
    "DUITAMA",
    "FUNZA",
    "FUNZA ITALCOL",
    "GIRON",
    "GUACARI",
    "LEBRIJA",
    "MEDELLIN",
    "OFICINA VIRTUAL",
    "PALERMO",
    "PALMIRA",
    "PEREIRA SM",
    "PTO LIBERTADOR",
    "PUERTO ANTIOQUIA",
    "RIVERPORT",
    "SAMACA",
    "SANTA MARTA",
    "TOCANCIPA",
    "UBATE",
    "VILLAVICENCIO",
    "YOPAL",
]


def get_destinos_por_origen(origen: str) -> list[str]:
    if not origen:
        return []

    with open("data/sicetac_combinaciones.json", encoding="utf-8") as f:
        combinaciones = json.load(f)

    return combinaciones.get(origen, [])


def load_origenes() -> list[str]:
    path = Path("data/sicetac_options.json")
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return payload.get("origen", [])


# --- 3. Sección de instrucciones colapsable ---
with st.expander("📖 Guía rápida"):
    st.markdown(
        """
        **¿Qué estoy registrando?**
        Un precio de flete para una plaza (origen → destino) con un vehículo específico.

        **Ejemplo completo:**

        | Campo | Valor |
        |---|---|
        | COD vehículo | 3S3 |
        | Origen | Bogotá |
        | Destino | Medellín |
        | Valor flete | $1,500,000 |
        | Tipo | Por viaje |
        | Fuente | SICETAC |
        | Agencia | BOGOTA |

        **Consejos:**
        - El **valor flete** debe ser el precio total acordado.
        - La **fuente** indica quién proporcionó el precio (cliente, conductor, sistema).
        - La **agencia** es la sucursal responsable del flete.
        """
    )

# --- 4. Valores sugeridos basados en historial ---
ultimos = obtener_ultimos_registros(5)
if ultimos:
    st.subheader("📋 Registros recientes")
    cols = st.columns(len(ultimos))
    for i, registro in enumerate(ultimos):
        with cols[i]:
            label = f"{registro.origen} → {registro.destino}\n${registro.tarifa:,.0f}"
            if st.button(
                label,
                key=f"reciente_{registro.id}",
                use_container_width=True,
                help="Clic para usar estos datos",
            ):
                st.session_state.form_origen = registro.origen
                st.session_state.form_destino = registro.destino
                st.session_state.form_tarifa = 0
                st.session_state.form_tipo_flete = registro.tipo_flete
                st.session_state.form_fuente = registro.fuente
                st.session_state.form_agencia = registro.agencia
                st.session_state.form_cod_vehiculo = registro.cod_vehiculo
                st.rerun()
    st.divider()

# --- Datos base ---
origenes = load_origenes()

# --- 1. Tooltips + 2. Validación visual ---

# COD vehículo
cod_vehiculo = st.selectbox(
    "COD vehiculo",
    [c["id"] for c in CONFIGURACIONES_VEHICULO],
    key="form_cod_vehiculo",
    format_func=lambda cod: f"{cod} — {next((c['valor'] for c in CONFIGURACIONES_VEHICULO if c['id'] == cod), '')}",
)

# Origen con validación visual
col_origen, col_status_origen = st.columns([5, 1])
with col_origen:
    origen = st.selectbox(
        "Ciudad de origen",
        ["", *origenes],
        key="form_origen",
    )
with col_status_origen:
    st.markdown("")
    st.markdown("")
    st.markdown("✅" if origen else "❌")
st.caption("Ciudad de origen del flete")

# Destino con validación visual
destinos_disponibles = get_destinos_por_origen(origen)
col_destino, col_status_destino = st.columns([5, 1])
with col_destino:
    destino = st.selectbox(
        "Ciudad de destino",
        ["", *destinos_disponibles],
        key="form_destino",
    )
with col_status_destino:
    st.markdown("")
    st.markdown("")
    st.markdown("✅" if destino else "❌")
st.caption("Ciudad de destino del flete")

st.divider()
st.subheader("Información del flete")

# Valor flete con validación visual
col_tarifa, col_formato, col_status_tarifa = st.columns([3, 2, 1])
with col_tarifa:
    tarifa = st.number_input(
        "Valor flete ($)",
        min_value=0,
        value=0,
        step=1000,
        format="%d",
        key="form_tarifa",
    )
with col_formato:
    st.write("Valor formateado")
    if tarifa > 0:
        st.markdown(f"### ${tarifa:,.0f}")
    else:
        st.write("_Ingrese un valor_")
with col_status_tarifa:
    st.markdown("")
    st.markdown("")
    st.markdown("✅" if tarifa > 0 else "❌")
st.caption("Valor total del flete en pesos colombianos")

# Tipo de flete
tipo_flete = st.selectbox(
    "Tipo de flete",
    ["Por viaje", "Por tonelada"],
    key="form_tipo_flete",
)
st.caption("Por viaje: precio fijo por ruta. Por tonelada: precio variable según carga.")

# Fuente con validación visual
col_fuente, col_status_fuente = st.columns([5, 1])
with col_fuente:
    fuente = st.text_input(
        "Fuente",
        placeholder="Cliente, Conductor o otros",
        key="form_fuente",
    )
with col_status_fuente:
    st.markdown("")
    st.markdown("")
    st.markdown("✅" if fuente.strip() else "❌")
st.caption("¿De dónde obtuviste el precio? Cliente, Conductor, SICETAC, u otros")

# Agencia
agencia = st.selectbox(
    "Agencia",
    AGENCIAS,
    key="form_agencia",
)
st.caption("Agencia o sucursal responsable del flete")

# --- 5. Indicador de progreso ---
campos_totales = 4
campos_completos = sum(
    [
        bool(origen),
        bool(destino),
        tarifa > 0,
        bool(fuente.strip()),
    ]
)
progreso = campos_completos / campos_totales
st.progress(progreso, text=f"Completado: {campos_completos}/{campos_totales}")

# Validación de campos obligatorios
campos_obligatorios = {
    "Origen": origen,
    "Destino": destino,
    "Valor flete": tarifa > 0,
    "Fuente": fuente.strip(),
}
campos_faltantes = [
    nombre for nombre, valor in campos_obligatorios.items() if not valor
]
todo_completo = len(campos_faltantes) == 0

st.divider()

if origen and destino:
    with st.container(border=True):
        st.markdown("### 📋 Resumen del registro")
        st.markdown(
            f"""
| Campo | Valor |
|---|---|
| 🚛 **Configuración** | `{cod_vehiculo}` |
| 📍 **Plaza** | `{origen} → {destino}` |
| 💰 **Valor flete** | `${tarifa:,.0f}` |
| 📊 **Tipo** | `{tipo_flete if tipo_flete else "_Sin especificar_"}` |
| 📎 **Fuente** | `{fuente if fuente else "_Sin especificar_"}` |
| 🏢 **Agencia** | `{agencia if agencia else "_Sin especificar_"}` |
        """
        )

        if not todo_completo:
            st.warning(f"⚠️ Campos pendientes: {', '.join(campos_faltantes)}")

        st.divider()
        guardar_clicked = st.button(
            "💾 Guardar registro",
            type="primary",
            use_container_width=True,
            disabled=not todo_completo,
        )
        if guardar_clicked:
            with st.spinner("Guardando registro..."):
                resultado = guardar_flete(
                    cod_vehiculo=cod_vehiculo,
                    origen=origen,
                    destino=destino,
                    tarifa=tarifa,
                    tipo_flete=tipo_flete,
                    fuente=fuente,
                    agencia=agencia,
                )
                if resultado:
                    st.success("✅ Registro guardado correctamente en la base de datos.")
                else:
                    st.error("❌ No se pudo guardar el registro. Revisa la conexión a BD.")
else:
    st.info("Selecciona origen y destino para ver el resumen.")
