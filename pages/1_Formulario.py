"""Página de formulario independiente."""

import json
from pathlib import Path

import streamlit as st

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


origenes = load_origenes()

cod_vehiculo = st.selectbox(
    "COD vehiculo",
    [c["id"] for c in CONFIGURACIONES_VEHICULO],
)

origen = st.selectbox(
    "Ciudad de origen",
    ["", *origenes],
    key="form_origen",
)

destinos_disponibles = get_destinos_por_origen(origen)

destino = st.selectbox(
    "Ciudad de destino",
    ["", *destinos_disponibles],
    key="form_destino",
)

st.divider()
st.subheader("Información del flete")

col_tarifa, col_formato = st.columns([3, 2])
with col_tarifa:
    tarifa = st.number_input(
        "Valor flete ($)", min_value=0, value=0, step=1000, format="%d"
    )
with col_formato:
    st.write("Valor formateado")
    if tarifa > 0:
        st.markdown(f"### ${tarifa:,.0f}")
    else:
        st.write("_Ingrese un valor_")

tipo_flete = st.selectbox(
    "Tipo de flete",
    ["", "Fijo", "Variable", "Por viaje", "Por tonelada", "Por km"],
)

col_fuente, col_agencia = st.columns(2)
with col_fuente:
    fuente = st.text_input("Fuente", placeholder="Ej: SICETAC, RNDC, Cliente...")
with col_agencia:
    agencia = st.text_input("Agencia", placeholder="Nombre de la agencia")

# Validación de campos obligatorios
campos_obligatorios = {
    "Origen": origen,
    "Destino": destino,
    "Valor flete": tarifa > 0,
    "Tipo de flete": tipo_flete,
    "Fuente": fuente.strip(),
    "Agencia": agencia.strip(),
}
campos_faltantes = [
    nombre for nombre, valor in campos_obligatorios.items() if not valor
]
todo_completo = len(campos_faltantes) == 0

st.divider()

if origen and destino:
    with st.container(border=True):
        st.markdown("### 📋 Resumen del registro")
        st.markdown(f"""
| Campo | Valor |
|---|---|
| 🚛 **Configuración** | `{cod_vehiculo}` |
| 📍 **Plaza** | `{origen} → {destino}` |
| 💰 **Valor flete** | `${tarifa:,.0f}` |
| 📊 **Tipo** | `{tipo_flete if tipo_flete else "_Sin especificar_"}` |
| 📎 **Fuente** | `{fuente if fuente else "_Sin especificar_"}` |
| 🏢 **Agencia** | `{agencia if agencia else "_Sin especificar_"}` |
        """)

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
            st.success("✅ Registro guardado correctamente.")
else:
    st.info("Selecciona origen y destino para ver el resumen.")
