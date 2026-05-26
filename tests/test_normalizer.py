"""Tests para app/nlp/normalizer.py — fuzzy_match_best y normalizar_municipios."""

from typing import ClassVar

import pytest

from app.nlp.normalizer import (
    fuzzy_match_best,
    normalizar_municipios,
    normalizar_sicetac_a_rndc,
)

# ─────────────────────────────────────────────
# fuzzy_match_best
# ─────────────────────────────────────────────


class TestFuzzyMatchBest:
    LISTA: ClassVar[list[str]] = [
        "MEDELLIN ANTIOQUIA",
        "BOGOTA BOGOTA D. C.",
        "CALI VALLE DEL CAUCA",
        "BARRANQUILLA ATLANTICO",
    ]

    def test_match_exacto(self):
        result = fuzzy_match_best("medellin antioquia", self.LISTA)
        assert result is not None
        assert result[0] == "MEDELLIN ANTIOQUIA"

    def test_match_con_umbral_bajo_retorna_resultado(self):
        result = fuzzy_match_best("medellin", self.LISTA, threshold=50)
        assert result is not None

    def test_umbral_muy_alto_rechaza(self):
        result = fuzzy_match_best("xyz123", self.LISTA, threshold=99)
        assert result is None

    def test_lista_vacia(self):
        result = fuzzy_match_best("MEDELLIN", [])
        assert result is None

    def test_query_vacio_retorna_none(self):
        result = fuzzy_match_best("", self.LISTA)
        assert result is None

    def test_retorna_tupla_con_tres_elementos(self):
        result = fuzzy_match_best("bogota", self.LISTA)
        assert result is not None
        assert len(result) == 3
        text, score, index = result
        assert isinstance(text, str)
        assert isinstance(score, float)
        assert isinstance(index, int)

    def test_score_es_mayor_o_igual_al_umbral(self):
        result = fuzzy_match_best("cali", self.LISTA, threshold=60)
        assert result is not None
        assert result[1] >= 60

    def test_match_parcial_con_token_set_ratio(self):
        # token_set_ratio es tolerante con palabras adicionales
        result = fuzzy_match_best("barranquilla", self.LISTA, threshold=80)
        assert result is not None
        assert "BARRANQUILLA" in result[0]


# ─────────────────────────────────────────────
# normalizar_municipios (función heredada)
# ─────────────────────────────────────────────


class TestNormalizarMunicipios:
    LISTA_MUNICIPIOS: ClassVar[list[str]] = [
        "MEDELLIN ANTIOQUIA",
        "BOGOTA BOGOTA D. C.",
        "CALI VALLE DEL CAUCA",
        "BARRANQUILLA ATLANTICO",
        "BUCARAMANGA SANTANDER",
        "PEREIRA RISARALDA",
        "AGUA DE DIOS CUNDINAMARCA",
    ]

    def test_nombre_none_retorna_none(self):
        assert normalizar_municipios(None, self.LISTA_MUNICIPIOS) is None

    def test_lista_vacia_retorna_none(self):
        assert normalizar_municipios("MEDELLIN", []) is None

    def test_nombre_y_lista_vacios_retorna_none(self):
        assert normalizar_municipios(None, []) is None

    def test_match_exitoso_ciudad_exacta(self):
        # Busca por primera palabra (lista_cortada)
        result = normalizar_municipios("MEDELLIN", self.LISTA_MUNICIPIOS)
        assert result is not None
        assert "MEDELLIN" in result

    def test_match_exitoso_con_acento(self):
        result = normalizar_municipios("BOGOTÁ", self.LISTA_MUNICIPIOS)
        assert result is not None
        assert "BOGOTA" in result

    def test_umbral_por_defecto_rechaza_ruido(self):
        result = normalizar_municipios("XYZXYZ_INEXISTENTE", self.LISTA_MUNICIPIOS)
        assert result is None

    def test_umbral_personalizado_bajo(self):
        # Con umbral muy bajo, acepta casi cualquier cosa
        result = normalizar_municipios("PEREIRA", self.LISTA_MUNICIPIOS, umbral=40)
        assert result is not None


# ─────────────────────────────────────────────
# normalizar_sicetac_a_rndc — cobertura extendida
# ─────────────────────────────────────────────


class TestNormalizarSicetacARndc:
    LISTA_RNDC: ClassVar[list[str]] = [
        "MEDELLIN ANTIOQUIA",
        "RIONEGRO ANTIOQUIA",
        "AGUACHICA CESAR",
        "BOGOTA BOGOTA D. C.",
        "CALI VALLE DEL CAUCA",
        "CUCUTA NORTE DE SANTANDER",
        "AGUA DE DIOS CUNDINAMARCA",
        "SANTA MARTA MAGDALENA",
    ]

    def test_entrada_none_retorna_none(self):
        assert normalizar_sicetac_a_rndc(None, self.LISTA_RNDC, {}) is None

    def test_lista_vacia_retorna_none(self):
        assert normalizar_sicetac_a_rndc("MEDELLIN", [], {}) is None

    def test_hit_en_lookup(self):
        lookup = {"AEROPUERTO - RIONEGRO - ANTIOQUIA": "RIONEGRO ANTIOQUIA"}
        result = normalizar_sicetac_a_rndc(
            "AEROPUERTO - RIONEGRO - ANTIOQUIA", self.LISTA_RNDC, lookup
        )
        assert result == "RIONEGRO ANTIOQUIA"

    def test_hit_no_llama_fuzzy(self):
        # Cuando hay HIT en lookup, debe devolver exactamente el valor cacheado
        # incluso si la lista RNDC está vacía (no hace fuzzy)
        lookup = {"BOGOTÁ": "BOGOTA BOGOTA D. C."}
        result = normalizar_sicetac_a_rndc("BOGOTÁ", [], lookup)
        assert result == "BOGOTA BOGOTA D. C."

    def test_miss_fallback_tipo_a(self):
        result = normalizar_sicetac_a_rndc(
            "AEROPUERTO - RIONEGRO - ANTIOQUIA", self.LISTA_RNDC, {}
        )
        assert result == "RIONEGRO ANTIOQUIA"

    def test_miss_fallback_tipo_b(self):
        result = normalizar_sicetac_a_rndc("AGUACHICA-CESAR", self.LISTA_RNDC, {})
        assert result == "AGUACHICA CESAR"

    def test_miss_fallback_tipo_c_bogota(self):
        result = normalizar_sicetac_a_rndc("BOGOTÁ", self.LISTA_RNDC, {})
        assert result == "BOGOTA BOGOTA D. C."

    def test_miss_fallback_tipo_c_cali(self):
        result = normalizar_sicetac_a_rndc("CALI", self.LISTA_RNDC, {})
        assert result == "CALI VALLE DEL CAUCA"

    def test_miss_sin_match_retorna_none(self):
        # Entrada completamente inventada
        result = normalizar_sicetac_a_rndc(
            "ZZZBOGUSPLACE-XYZDEPTO", self.LISTA_RNDC, {}
        )
        assert result is None

    def test_cache_aside_guardado_en_lookup(self):
        lookup: dict[str, str] = {}
        normalizar_sicetac_a_rndc(
            "MEDELLIN - MEDELLIN - ANTIOQUIA", self.LISTA_RNDC, lookup
        )
        # Después del fallback exitoso, el resultado debe haber sido almacenado
        assert "MEDELLIN - MEDELLIN - ANTIOQUIA" in lookup

    def test_cache_aside_no_sobreescribe_hit_existente(self):
        lookup = {"BOGOTÁ": "MI_VALOR_CORRECTO"}
        normalizar_sicetac_a_rndc("BOGOTÁ", self.LISTA_RNDC, lookup)
        # El valor original no debe modificarse
        assert lookup["BOGOTÁ"] == "MI_VALOR_CORRECTO"

    def test_umbral_personalizado_permisivo(self):
        # Con umbral 0, cualquier candidato del mismo dpto debería resolver
        lista = ["ABCXYZ ANTIOQUIA"]
        result = normalizar_sicetac_a_rndc(
            "CUALQUIERCOSA - ABCXYZ - ANTIOQUIA", lista, {}, umbral=0
        )
        assert result == "ABCXYZ ANTIOQUIA"

    def test_departamento_norte_de_santander(self):
        result = normalizar_sicetac_a_rndc("CUCUTA", self.LISTA_RNDC, {})
        assert result == "CUCUTA NORTE DE SANTANDER"

    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("MEDELLIN - MEDELLIN - ANTIOQUIA", "MEDELLIN ANTIOQUIA"),
            ("BOGOTÁ", "BOGOTA BOGOTA D. C."),
            ("AGUACHICA-CESAR", "AGUACHICA CESAR"),
            ("AGUA DE DIOS - AGUA DE DIOS - CUNDINAMARCA", "AGUA DE DIOS CUNDINAMARCA"),
        ],
    )
    def test_normalizacion_parametrizada(self, entrada, esperado):
        result = normalizar_sicetac_a_rndc(entrada, self.LISTA_RNDC, {})
        assert result == esperado
