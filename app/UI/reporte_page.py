"""Página de reporte: resumen por agencia.

Muestra, por agencia, cuántos registros hay y la última fecha de registro.
Permite búsqueda por agencia, filtrado por rango de fechas y exportar el resumen a CSV.
"""

import io
from datetime import datetime

import pandas as pd
import streamlit as st
from sqlalchemy import func

from app.core import get_app_logger
from app.db.session import get_session_factory
from app.models.flete import FleteRegistro

logger = get_app_logger("reporte_page")


def render():
    st.title("📈 Reporte por Agencia")

    st.markdown(
        "Muestra la cantidad de registros por agencia y la última fecha de registro."
    )

    # Filtros sencillos
    busca = st.text_input("Buscar agencia (filtro)", value="")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        top_n = st.number_input("Mostrar top N agencias", min_value=1, max_value=500, value=50, step=1)
    with col_f2:
        filtrar_fechas = st.checkbox("Filtrar por rango de fechas")

    fecha_desde = None
    fecha_hasta = None
    if filtrar_fechas:
        c1, c2 = st.columns(2)
        with c1:
            fecha_desde = st.date_input("Fecha desde", value=None)
        with c2:
            fecha_hasta = st.date_input("Fecha hasta", value=None)

    # Query agregada
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        q = (
            session.query(
                FleteRegistro.agencia.label("agencia"),
                func.count(FleteRegistro.id).label("total"),
                func.max(FleteRegistro.creado_en).label("ultima"),
            )
            .group_by(FleteRegistro.agencia)
            .order_by(func.count(FleteRegistro.id).desc())
        )

        if busca:
            q = q.filter(FleteRegistro.agencia.ilike(f"%{busca}%"))

        # Aplicar filtro por rango de fechas si fue solicitado
        if filtrar_fechas and fecha_desde:
            # fecha_desde/fecha_hasta son date -> convertir a datetime
            start_dt = datetime.combine(fecha_desde, datetime.min.time())
            if fecha_hasta:
                end_dt = datetime.combine(fecha_hasta, datetime.max.time())
            else:
                end_dt = datetime.combine(fecha_desde, datetime.max.time())
            q = q.filter(FleteRegistro.creado_en >= start_dt, FleteRegistro.creado_en <= end_dt)

        rows = q.limit(top_n).all()
    except Exception as e:
        logger.error(f"Error consultando reporte por agencia: {e}")
        st.error("Error consultando la base de datos. Revisa los logs.")
        return
    finally:
        session.close()

    if not rows:
        st.info(
            "No se encontraron registros de fletes para las agencias seleccionadas."
        )
        return

    data = []
    for agencia, total, ultima in rows:
        fecha_str = (
            ultima.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(ultima, datetime)
            else (str(ultima) if ultima else "")
        )
        data.append({"agencia": agencia, "total": int(total), "ultima": fecha_str})

    df = pd.DataFrame(data)

    st.dataframe(df, use_container_width=True)

    # Export CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    st.download_button(
        "📥 Exportar CSV",
        data=csv_bytes,
        file_name="reporte_agencias.csv",
        mime="text/csv",
    )

    # KPI
    total_registros = df["total"].sum()
    total_agencias = df.shape[0]
    col1, col2 = st.columns(2)
    col1.metric("Agencias listadas", f"{total_agencias}")
    col2.metric("Registros (sum)", f"{total_registros}")

    st.caption(
        "Nota: este reporte agrupa por el valor literal de la columna `agencia` en los registros."
    )
        mime="text/csv",
    )

    # KPI
    total_registros = df["total"].sum()
    total_agencias = df.shape[0]
    col1, col2 = st.columns(2)
    col1.metric("Agencias listadas", f"{total_agencias}")
    col2.metric("Registros (sum)", f"{total_registros}")

    st.caption(
        "Nota: este reporte agrupa por el valor literal de la columna `agencia` en los registros."
    )
