"""Tests para app/services/query_service.py — fuzzy_match_best y consultar_ruta."""

from typing import ClassVar

import polars as pl
import pytest

from app.services.query_service import consultar_ruta, fuzzy_match_best

# ─────────────────────────────────────────────
# Fixtures reutilizables
# ─────────────────────────────────────────────


@pytest.fixture
def df_ruta():
    """DataFrame mínimo con el esquema que espera consultar_ruta."""
    return pl.DataFrame(
        {
            "COD_CONFIG_VEHICULO": ["C3S3", "C3S3", "C2"],
            "MUNICIPIOORIGEN": [
                "MEDELLIN ANTIOQUIA",
                "BOGOTA BOGOTA D. C.",
                "MEDELLIN ANTIOQUIA",
            ],
            "MUNICIPIODESTINO": [
                "BOGOTA BOGOTA D. C.",
                "CALI VALLE DEL CAUCA",
                "CALI VALLE DEL CAUCA",
            ],
            "VIAJESTOTALES": [10, 5, 3],
            "VALORESPAGADOS": [5_000_000, 3_000_000, 2_000_000],
            "VALOR_PROMEDIO_UNITARIO": [500_000.0, 600_000.0, 666_666.7],
        }
    )


# ─────────────────────────────────────────────
# fuzzy_match_best (query_service)
# ─────────────────────────────────────────────


class TestFuzzyMatchBestService:
    CANDIDATOS: ClassVar[list[str]] = [
        "MEDELLIN ANTIOQUIA",
        "BOGOTA BOGOTA D. C.",
        "CALI VALLE DEL CAUCA",
    ]

    def test_match_exacto(self):
        r = fuzzy_match_best("medellin antioquia", self.CANDIDATOS)
        assert r is not None
        assert r[0] == "MEDELLIN ANTIOQUIA"

    def test_sin_candidatos(self):
        assert fuzzy_match_best("MEDELLIN", []) is None

    def test_umbral_rechaza_ruido(self):
        assert fuzzy_match_best("XYZABC", self.CANDIDATOS, threshold=95) is None

    def test_retorna_tres_elementos(self):
        r = fuzzy_match_best("CALI", self.CANDIDATOS, threshold=50)
        assert r is not None
        assert len(r) == 3


# ─────────────────────────────────────────────
# consultar_ruta
# ─────────────────────────────────────────────


class TestConsultarRuta:
    def test_ruta_existente(self, df_ruta):
        r = consultar_ruta(df_ruta, "MEDELLIN ANTIOQUIA", "BOGOTA BOGOTA D. C.", "C3S3")
        assert len(r) == 1
        assert r["MUNICIPIOORIGEN"][0] == "MEDELLIN ANTIOQUIA"

    def test_ruta_inexistente(self, df_ruta):
        r = consultar_ruta(df_ruta, "TUMACO NARINO", "LETICIA AMAZONAS", "C3S3")
        assert len(r) == 0

    def test_configuracion_incorrecta_retorna_vacio(self, df_ruta):
        # Ruta existe pero configuración errónea
        r = consultar_ruta(
            df_ruta, "MEDELLIN ANTIOQUIA", "BOGOTA BOGOTA D. C.", "INEXISTENTE"
        )
        assert len(r) == 0

    def test_origen_none_retorna_dataframe_vacio(self, df_ruta):
        r = consultar_ruta(df_ruta, None, "BOGOTA BOGOTA D. C.", "C3S3")
        assert isinstance(r, pl.DataFrame)
        assert len(r) == 0

    def test_destino_none_retorna_dataframe_vacio(self, df_ruta):
        r = consultar_ruta(df_ruta, "MEDELLIN ANTIOQUIA", None, "C3S3")
        assert isinstance(r, pl.DataFrame)
        assert len(r) == 0

    def test_ambos_none_retorna_dataframe_vacio(self, df_ruta):
        r = consultar_ruta(df_ruta, None, None, "C3S3")
        assert isinstance(r, pl.DataFrame)
        assert len(r) == 0

    def test_retorna_polars_dataframe(self, df_ruta):
        r = consultar_ruta(df_ruta, "MEDELLIN ANTIOQUIA", "BOGOTA BOGOTA D. C.", "C3S3")
        assert isinstance(r, pl.DataFrame)

    def test_columnas_resultado(self, df_ruta):
        r = consultar_ruta(df_ruta, "MEDELLIN ANTIOQUIA", "BOGOTA BOGOTA D. C.", "C3S3")
        assert "MUNICIPIOORIGEN" in r.columns
        assert "MUNICIPIODESTINO" in r.columns
        assert "COD_CONFIG_VEHICULO" in r.columns

    def test_multiples_rutas_distintas_se_filtran(self, df_ruta):
        # La ruta C3S3 de MED→BOG existe y la de BOG→CAL también
        r1 = consultar_ruta(
            df_ruta, "MEDELLIN ANTIOQUIA", "BOGOTA BOGOTA D. C.", "C3S3"
        )
        r2 = consultar_ruta(
            df_ruta, "BOGOTA BOGOTA D. C.", "CALI VALLE DEL CAUCA", "C3S3"
        )
        assert len(r1) == 1
        assert len(r2) == 1
        # No se mezclan
        assert r1["MUNICIPIODESTINO"][0] != r2["MUNICIPIODESTINO"][0]
