"""Página de reporte: estado de registro por agencia.

Permite ver, para un rango de fechas, qué agencias registraron fletes y cuáles
no (semáforo ✅/❌), la cobertura total, un filtro rápido por estado, presets de
fecha y una alerta de agencias inactivas (sin registrar hace más de N días).
"""

import io
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import func

from app.core import get_app_logger
from app.db.session import get_session_factory
from app.models.flete import FleteRegistro
from app.UI.formulario_page import AGENCIAS

logger = get_app_logger("reporte_page")

# Lista maestra de agencias reales (se excluye el centinela "TODOS").
AGENCIAS_REALES = [a for a in AGENCIAS if a != "TODOS"]


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serializa un DataFrame a un archivo Excel (.xlsx) en memoria."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")
    buffer.seek(0)
    return buffer.read()


def _rango_por_preset(preset: str) -> tuple[date, date]:
    """Traduce un preset de fecha a un rango (desde, hasta)."""
    hoy = date.today()
    if preset == "Hoy":
        return hoy, hoy
    if preset == "Ayer":
        ayer = hoy - timedelta(days=1)
        return ayer, ayer
    if preset == "Esta semana":
        # Lunes de la semana actual hasta hoy
        return hoy - timedelta(days=hoy.weekday()), hoy
    if preset == "Este mes":
        return hoy.replace(day=1), hoy
    # Personalizado: el valor real lo definen los date_input del formulario
    return hoy.replace(day=1), hoy


def _consultar_rango(session, fecha_desde: date, fecha_hasta: date) -> dict[str, int]:
    """Devuelve {agencia: cantidad_registros} dentro del rango indicado."""
    start_dt = datetime.combine(fecha_desde, datetime.min.time())
    end_dt = datetime.combine(fecha_hasta, datetime.max.time())
    filas = (
        session.query(
            FleteRegistro.agencia.label("agencia"),
            func.count(FleteRegistro.id).label("total"),
        )
        .filter(FleteRegistro.creado_en >= start_dt)
        .filter(FleteRegistro.creado_en <= end_dt)
        .group_by(FleteRegistro.agencia)
        .all()
    )
    return {agencia: int(total) for agencia, total in filas if agencia}


def _consultar_ultima_global(session) -> dict[str, datetime]:
    """Devuelve {agencia: última_fecha_registro} sobre todo el histórico."""
    filas = (
        session.query(
            FleteRegistro.agencia.label("agencia"),
            func.max(FleteRegistro.creado_en).label("ultima"),
        )
        .group_by(FleteRegistro.agencia)
        .all()
    )
    return {agencia: ultima for agencia, ultima in filas if agencia}


def _construir_tabla(
    rango_map: dict[str, int],
    ultima_map: dict[str, datetime],
    umbral_dias: int,
    hoy: date | None = None,
) -> pd.DataFrame:
    """Arma la tabla de estado por agencia combinando el rango y el histórico.

    Incluye siempre todas las agencias de la lista maestra (más cualquier
    agencia presente en los datos que no esté en ella) y ordena primero las que
    faltan en el rango, luego las más rezagadas.
    """
    hoy = hoy or date.today()

    agencias = list(AGENCIAS_REALES)
    for ag in set(rango_map) | set(ultima_map):
        if ag not in agencias:
            agencias.append(ag)

    filas = []
    for agencia in agencias:
        registros = rango_map.get(agencia, 0)
        registro_en_rango = registros > 0

        ultima_dt = ultima_map.get(agencia)
        if ultima_dt is not None:
            ultima_txt = ultima_dt.strftime("%Y-%m-%d")
            dias_sin = (hoy - ultima_dt.date()).days
        else:
            ultima_txt = "Nunca"
            dias_sin = None

        inactiva = (dias_sin is None) or (dias_sin > umbral_dias)

        filas.append(
            {
                "Agencia": agencia,
                "Estado": "✅ Registró" if registro_en_rango else "❌ Sin registros",
                "Registros": registros,
                "Última vez": ultima_txt,
                "Días sin registrar": dias_sin if dias_sin is not None else "—",
                "Alerta": "⚠️ Inactiva" if inactiva else "",
                "_registro_en_rango": registro_en_rango,
                "_dias_orden": dias_sin if dias_sin is not None else 10**6,
            }
        )

    df = pd.DataFrame(filas)
    return df.sort_values(
        by=["_registro_en_rango", "_dias_orden"],
        ascending=[True, False],
    ).reset_index(drop=True)


def render():
    st.title("📈 Reporte de registro por agencia")
    st.markdown(
        "Muestra, para el rango elegido, **qué agencias registraron y cuáles no**, "
        "junto con la cobertura y una alerta de agencias inactivas."
    )

    # ── 4. Presets de fecha rápidos ─────────────────────────────────────────
    preset = st.radio(
        "Rango de fechas",
        ["Hoy", "Ayer", "Esta semana", "Este mes", "Personalizado"],
        horizontal=True,
    )

    if preset == "Personalizado":
        c1, c2 = st.columns(2)
        with c1:
            fecha_desde = st.date_input("Desde", value=date.today().replace(day=1))
        with c2:
            fecha_hasta = st.date_input("Hasta", value=date.today())
        if fecha_desde > fecha_hasta:
            st.warning("La fecha 'Desde' no puede ser mayor que 'Hasta'.")
            return
    else:
        fecha_desde, fecha_hasta = _rango_por_preset(preset)

    st.caption(f"Rango analizado: **{fecha_desde} → {fecha_hasta}**")

    # ── 7. Umbral de inactividad ────────────────────────────────────────────
    umbral_dias = st.number_input(
        "Marcar como inactiva si no registra hace más de (días)",
        min_value=1,
        max_value=365,
        value=7,
        step=1,
        help="La alerta de inactividad es global (independiente del rango de fechas).",
    )

    # ── Consultas a la base de datos ────────────────────────────────────────
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        rango_map = _consultar_rango(session, fecha_desde, fecha_hasta)
        ultima_map = _consultar_ultima_global(session)
    except Exception as e:
        logger.error(f"Error consultando reporte por agencia: {e}")
        st.error("Error consultando la base de datos. Revisa los logs.")
        return
    finally:
        session.close()

    df = _construir_tabla(rango_map, ultima_map, umbral_dias)

    # ── 2. KPI de cobertura ─────────────────────────────────────────────────
    total_agencias = len(df)
    registraron = int(df["_registro_en_rango"].sum())
    faltantes = total_agencias - registraron
    inactivas = int((df["Alerta"] != "").sum())
    cobertura = (registraron / total_agencias * 100) if total_agencias else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cobertura", f"{cobertura:.0f}%", f"{registraron}/{total_agencias}")
    col2.metric("Registraron", f"{registraron}")
    col3.metric("Sin registrar", f"{faltantes}")
    col4.metric("Inactivas", f"{inactivas}")

    # ── 7. Alerta de agencias inactivas ─────────────────────────────────────
    agencias_inactivas = df.loc[df["Alerta"] != "", "Agencia"].tolist()
    if agencias_inactivas:
        st.warning(
            f"⚠️ {len(agencias_inactivas)} agencia(s) sin registrar hace más de "
            f"{umbral_dias} días: {', '.join(agencias_inactivas)}"
        )

    # ── 3. Filtro rápido por estado ─────────────────────────────────────────
    filtro = st.radio(
        "Ver",
        ["Todas", "Solo registraron", "Solo faltantes"],
        horizontal=True,
    )

    df_view = df
    if filtro == "Solo registraron":
        df_view = df[df["_registro_en_rango"]]
    elif filtro == "Solo faltantes":
        df_view = df[~df["_registro_en_rango"]]

    columnas_visibles = [
        "Agencia",
        "Estado",
        "Registros",
        "Última vez",
        "Días sin registrar",
        "Alerta",
    ]
    df_view = df_view[columnas_visibles]

    # ── 1. Tabla de estado con semáforo ─────────────────────────────────────
    if df_view.empty:
        st.info("No hay agencias que coincidan con el filtro seleccionado.")
    else:
        st.dataframe(df_view, use_container_width=True, hide_index=True)

    # Exportar a Excel (respeta el filtro activo)
    st.download_button(
        "📊 Exportar Excel",
        data=_to_excel_bytes(df_view),
        file_name="reporte_agencias.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.caption(
        "El estado ✅/❌ y la columna *Registros* corresponden al rango elegido. "
        "*Última vez* y *Días sin registrar* son globales (todo el histórico)."
    )
