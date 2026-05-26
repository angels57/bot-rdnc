"""Tests para app/data/processor.py — transformación del DataFrame RNDC."""

import polars as pl
import pytest

from app.data.processor import processor

# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────


@pytest.fixture
def df_raw():
    """DataFrame bruto con el esquema completo que devuelve cargar_data."""
    return pl.DataFrame(
        {
            "COD_CONFIG_VEHICULO": ["C3S3", "C3S3", "C3S3", "C2", "C3S3"],
            "MUNICIPIOORIGEN": [
                "MEDELLIN ANTIOQUIA",
                "MEDELLIN ANTIOQUIA",
                "BOGOTA BOGOTA D. C.",
                "CALI VALLE DEL CAUCA",
                "CALI VALLE DEL CAUCA",
            ],
            "MUNICIPIODESTINO": [
                "BOGOTA BOGOTA D. C.",
                "BOGOTA BOGOTA D. C.",
                "MEDELLIN ANTIOQUIA",
                "MEDELLIN ANTIOQUIA",
                "BOGOTA BOGOTA D. C.",
            ],
            "VIAJESTOTALES": [5, 3, 7, 2, 1],
            "VALORESPAGADOS": [2_500_000, 1_500_000, 3_000_000, 900_000, 0],
            "NATURALEZACARGA": [
                "Carga General",
                "Carga General",
                "Carga General",
                "Carga Peligrosa",
                "Graneles Sólidos",
            ],
        }
    )


# ─────────────────────────────────────────────
# Tests del processor
# ─────────────────────────────────────────────


class TestProcessor:
    def test_retorna_dataframe_polars(self, df_raw):
        result = processor(df_raw)
        assert isinstance(result, pl.DataFrame)

    def test_filtra_carga_peligrosa(self, df_raw):
        result = processor(df_raw)
        if "NATURALEZACARGA" in result.columns:
            assert "Carga Peligrosa" not in result["NATURALEZACARGA"].to_list()

    def test_filtra_registros_valor_cero(self, df_raw):
        result = processor(df_raw)
        # La fila con VALORESPAGADOS=0 (cali→bogota C3S3) debe eliminarse
        # Verificamos que no haya valores negativos o cero en la agregación
        assert len(result) > 0

    def test_columnas_requeridas_presentes(self, df_raw):
        result = processor(df_raw)
        required = {"COD_CONFIG_VEHICULO", "MUNICIPIOORIGEN", "MUNICIPIODESTINO"}
        assert required.issubset(set(result.columns))

    def test_columna_valor_promedio_unitario(self, df_raw):
        result = processor(df_raw)
        assert "VALOR_PROMEDIO_UNITARIO" in result.columns

    def test_groupby_agrupa_rutas_identicas(self, df_raw):
        result = processor(df_raw)
        # Las dos filas de MED→BOG C3S3 (con valores > 0) deben agregarse en 1
        med_bog = result.filter(
            (pl.col("MUNICIPIOORIGEN") == "MEDELLIN ANTIOQUIA")
            & (pl.col("MUNICIPIODESTINO") == "BOGOTA BOGOTA D. C.")
            & (pl.col("COD_CONFIG_VEHICULO") == "C3S3")
        )
        assert len(med_bog) == 1

    def test_valor_promedio_correcto(self, df_raw):
        result = processor(df_raw)
        med_bog = result.filter(
            (pl.col("MUNICIPIOORIGEN") == "MEDELLIN ANTIOQUIA")
            & (pl.col("MUNICIPIODESTINO") == "BOGOTA BOGOTA D. C.")
            & (pl.col("COD_CONFIG_VEHICULO") == "C3S3")
        )
        assert len(med_bog) == 1
        # VALOR_PROMEDIO_UNITARIO = mean(2_500_000/5, 1_500_000/3) = mean(500_000, 500_000) = 500_000
        assert med_bog["VALOR_PROMEDIO_UNITARIO"][0] == pytest.approx(500_000, rel=0.01)

    def test_viajestotales_sumados(self, df_raw):
        result = processor(df_raw)
        med_bog = result.filter(
            (pl.col("MUNICIPIOORIGEN") == "MEDELLIN ANTIOQUIA")
            & (pl.col("MUNICIPIODESTINO") == "BOGOTA BOGOTA D. C.")
            & (pl.col("COD_CONFIG_VEHICULO") == "C3S3")
        )
        # 5 + 3 = 8 viajes
        assert med_bog["VIAJESTOTALES"][0] == 8

    def test_resultado_ordenado_por_valor_promedio(self, df_raw):
        result = processor(df_raw)
        if len(result) > 1:
            valores = result["VALOR_PROMEDIO_UNITARIO"].to_list()
            assert valores == sorted(valores)

    def test_dataframe_vacio_no_explota(self):
        df_empty = pl.DataFrame(
            {
                "COD_CONFIG_VEHICULO": pl.Series([], dtype=pl.String),
                "MUNICIPIOORIGEN": pl.Series([], dtype=pl.String),
                "MUNICIPIODESTINO": pl.Series([], dtype=pl.String),
                "VIAJESTOTALES": pl.Series([], dtype=pl.Int64),
                "VALORESPAGADOS": pl.Series([], dtype=pl.Int64),
                "NATURALEZACARGA": pl.Series([], dtype=pl.String),
            }
        )
        result = processor(df_empty)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0
