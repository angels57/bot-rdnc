"""Tests exhaustivos para app/nlp/parser.py."""

import pytest

from app.nlp.parser import DPTOS_COLOMBIA, clean_text, parse_rndc, parse_sicetac

# ─────────────────────────────────────────────
# clean_text
# ─────────────────────────────────────────────


class TestCleanText:
    def test_elimina_tildes(self):
        assert clean_text("Bogotá") == "bogota"
        assert clean_text("Medellín") == "medellin"
        assert clean_text("NARIÑO") == "narino"
        assert clean_text("Quibdó") == "quibdo"

    def test_convierte_a_minusculas(self):
        assert clean_text("ANTIOQUIA") == "antioquia"
        assert clean_text("Meta") == "meta"

    def test_elimina_espacios_al_inicio_y_fin(self):
        assert clean_text("  BOGOTA  ") == "bogota"
        assert clean_text("\tVALLE DEL CAUCA\n") == "valle del cauca"

    def test_string_vacio(self):
        assert clean_text("") == ""

    def test_solo_espacios(self):
        assert clean_text("   ") == ""

    def test_caracteres_especiales_se_conservan(self):
        # Puntos y comas deben conservarse
        result = clean_text("BOGOTA D. C.")
        assert "bogota" in result
        assert "d." in result or "d" in result

    def test_texto_sin_tildes_no_cambia(self):
        assert clean_text("CALDAS") == "caldas"
        assert clean_text("META") == "meta"


# ─────────────────────────────────────────────
# parse_sicetac
# ─────────────────────────────────────────────


class TestParseSicetac:
    # ── Tipo A: 3 partes (LUGAR - MUNICIPIO - DEPARTAMENTO) ──

    def test_tipo_a_basico(self):
        r = parse_sicetac("ABEJORRAL - ABEJORRAL - ANTIOQUIA")
        assert r["lugar"] == "ABEJORRAL"
        assert r["municipio"] == "ABEJORRAL"
        assert r["departamento"] == "ANTIOQUIA"

    def test_tipo_a_lugar_distinto_al_municipio(self):
        r = parse_sicetac("AEROPUERTO - RIONEGRO - ANTIOQUIA")
        assert r["lugar"] == "AEROPUERTO"
        assert r["municipio"] == "RIONEGRO"
        assert r["departamento"] == "ANTIOQUIA"

    def test_tipo_a_municipio_nombre_compuesto(self):
        r = parse_sicetac("AGUA DE DIOS - AGUA DE DIOS - CUNDINAMARCA")
        assert r["municipio"] == "AGUA DE DIOS"
        assert r["departamento"] == "CUNDINAMARCA"

    def test_tipo_a_departamento_compuesto(self):
        r = parse_sicetac("ABREGO - ABREGO - NORTE DE SANTANDER")
        assert r["municipio"] == "ABREGO"
        assert r["departamento"] == "NORTE DE SANTANDER"

    def test_tipo_a_departamento_valle_del_cauca(self):
        r = parse_sicetac("ALCALA - ALCALA - VALLE DEL CAUCA")
        assert r["municipio"] == "ALCALA"
        assert r["departamento"] == "VALLE DEL CAUCA"

    def test_tipo_a_bogota_dc(self):
        r = parse_sicetac("CONCEPCION - BOGOTA DISTRITO CAPITAL - BOGOTA D. C.")
        assert r["municipio"] == "BOGOTA DISTRITO CAPITAL"
        assert r["departamento"] == "BOGOTA D. C."

    # ── Tipo A con 4+ partes (casos trampa) ──

    def test_tipo_a_cuatro_partes(self):
        r = parse_sicetac("BUENOS AIRES - LAS PAVAS - CANALETE - CORDOBA")
        assert r["lugar"] == "BUENOS AIRES - LAS PAVAS"
        assert r["municipio"] == "CANALETE"
        assert r["departamento"] == "CORDOBA"

    def test_tipo_a_zona_bananera(self):
        r = parse_sicetac("PRADO - SEVILLA - ZONA BANANERA - MAGDALENA")
        assert r["municipio"] == "ZONA BANANERA"
        assert r["departamento"] == "MAGDALENA"

    # ── Tipo B: 2 partes (MUNICIPIO-DEPARTAMENTO) ──

    def test_tipo_b_sin_espacios(self):
        r = parse_sicetac("AGUACHICA-CESAR")
        assert r["lugar"] == "AGUACHICA"
        assert r["municipio"] == "AGUACHICA"
        assert r["departamento"] == "CESAR"

    def test_tipo_b_con_espacios(self):
        r = parse_sicetac("ARBOLETES - ANTIOQUIA")
        assert r["lugar"] == "ARBOLETES"
        assert r["municipio"] == "ARBOLETES"
        assert r["departamento"] == "ANTIOQUIA"

    def test_tipo_b_con_tilde(self):
        r = parse_sicetac("FUSAGASUGÁ-CUNDINAMARCA")
        assert r["municipio"] == "FUSAGASUGÁ"
        assert r["departamento"] == "CUNDINAMARCA"

    def test_tipo_b_departamento_nario_con_tilde(self):
        r = parse_sicetac("IPIALES-NARIÑO")
        assert r["municipio"] == "IPIALES"
        assert r["departamento"] == "NARIÑO"

    def test_tipo_b_departamento_boyaca_con_tilde(self):
        r = parse_sicetac("SOGAMOSO-BOYACÁ")
        assert r["municipio"] == "SOGAMOSO"
        assert r["departamento"] == "BOYACÁ"

    # ── Tipo B con en-dash Unicode ──

    def test_tipo_a_con_en_dash_unicode(self):
        r = parse_sicetac("ADJUNTAS - AGUACHICA – CESAR")  # noqa: RUF001
        assert r["lugar"] == "ADJUNTAS"
        assert r["municipio"] == "AGUACHICA"
        assert r["departamento"] == "CESAR"

    # ── Tipo C: Solo nombre ──

    def test_tipo_c_sin_acento(self):
        r = parse_sicetac("ARMENIA")
        assert r["lugar"] == "ARMENIA"
        assert r["municipio"] == "ARMENIA"
        assert r["departamento"] == ""

    def test_tipo_c_con_acento(self):
        r = parse_sicetac("BOGOTÁ")
        assert r["lugar"] == "BOGOTÁ"
        assert r["municipio"] == "BOGOTÁ"
        assert r["departamento"] == ""

    def test_tipo_c_nombre_compuesto(self):
        r = parse_sicetac("GUADALAJARA DE BUGA")
        assert r["municipio"] == "GUADALAJARA DE BUGA"
        assert r["departamento"] == ""

    # ── Entradas con espacios al inicio/fin ──

    def test_trim_espacios_entrada(self):
        r = parse_sicetac("  AGUACHICA-CESAR  ")
        assert r["municipio"] == "AGUACHICA"
        assert r["departamento"] == "CESAR"

    # ── Claves siempre presentes ──

    def test_retorna_tres_claves_siempre(self):
        for entrada in [
            "BOGOTÁ",
            "AGUACHICA-CESAR",
            "AEROPUERTO - RIONEGRO - ANTIOQUIA",
        ]:
            r = parse_sicetac(entrada)
            assert "lugar" in r
            assert "municipio" in r
            assert "departamento" in r


# ─────────────────────────────────────────────
# parse_rndc
# ─────────────────────────────────────────────


class TestParseRndc:
    def test_municipio_departamento_simple(self):
        r = parse_rndc("ABEJORRAL ANTIOQUIA")
        assert r["municipio"] == "ABEJORRAL"
        assert r["departamento"] == "ANTIOQUIA"

    def test_departamento_multi_palabra_valle(self):
        r = parse_rndc("CALI VALLE DEL CAUCA")
        assert r["municipio"] == "CALI"
        assert r["departamento"] == "VALLE DEL CAUCA"

    def test_departamento_multi_palabra_norte_santander(self):
        r = parse_rndc("CUCUTA NORTE DE SANTANDER")
        assert r["municipio"] == "CUCUTA"
        assert r["departamento"] == "NORTE DE SANTANDER"

    def test_municipio_multi_palabra(self):
        r = parse_rndc("AGUA DE DIOS CUNDINAMARCA")
        assert r["municipio"] == "AGUA DE DIOS"
        assert r["departamento"] == "CUNDINAMARCA"

    def test_municipio_con_barrio(self):
        r = parse_rndc("AEROPUERTO RIONEGRO ANTIOQUIA")
        assert r["municipio"] == "AEROPUERTO RIONEGRO"
        assert r["departamento"] == "ANTIOQUIA"

    def test_bogota_dc(self):
        r = parse_rndc("BOGOTA BOGOTA D. C.")
        assert r["departamento"] == "BOGOTA D. C."
        assert "BOGOTA" in r["municipio"]

    def test_sin_departamento_conocido(self):
        # Si no se reconoce el departamento, el texto completo va en municipio
        r = parse_rndc("LUGAR DESCONOCIDO")
        assert r["departamento"] == ""
        assert r["municipio"] == "LUGAR DESCONOCIDO"

    def test_trim_espacios(self):
        r = parse_rndc("  MEDELLIN ANTIOQUIA  ")
        assert r["municipio"] == "MEDELLIN"
        assert r["departamento"] == "ANTIOQUIA"

    def test_retorna_dos_claves_siempre(self):
        for entrada in [
            "MEDELLIN ANTIOQUIA",
            "BOGOTA BOGOTA D. C.",
            "CALI VALLE DEL CAUCA",
        ]:
            r = parse_rndc(entrada)
            assert "municipio" in r
            assert "departamento" in r


# ─────────────────────────────────────────────
# DPTOS_COLOMBIA
# ─────────────────────────────────────────────


class TestDptosColombia:
    def test_contiene_departamentos_clave(self):
        assert "ANTIOQUIA" in DPTOS_COLOMBIA
        assert "CUNDINAMARCA" in DPTOS_COLOMBIA
        assert "VALLE DEL CAUCA" in DPTOS_COLOMBIA
        assert "NORTE DE SANTANDER" in DPTOS_COLOMBIA
        assert "BOGOTA D. C." in DPTOS_COLOMBIA

    def test_total_razonable(self):
        # Colombia tiene 32 departamentos + Bogotá D.C.
        assert len(DPTOS_COLOMBIA) >= 30

    def test_es_un_set(self):
        assert isinstance(DPTOS_COLOMBIA, set)

    def test_sin_duplicados(self):
        assert len(DPTOS_COLOMBIA) == len(set(DPTOS_COLOMBIA))


# ─────────────────────────────────────────────
# Parametrize: casos reales del JSON de SICETAC
# ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("entrada", "esperado_municipio", "esperado_dpto"),
    [
        ("ACACIAS - ACACIAS - META", "ACACIAS", "META"),
        ("ARAUCA - ARAUCA - ARAUCA", "ARAUCA", "ARAUCA"),
        ("BELLO - BELLO - ANTIOQUIA", "BELLO", "ANTIOQUIA"),
        ("CALI", "CALI", ""),
        ("BARRANQUILLA", "BARRANQUILLA", ""),
        ("CARTAGENA", "CARTAGENA", ""),
        ("CAJICA - CUNDINAMARCA", "CAJICA", "CUNDINAMARCA"),
        ("CARTAGO-VALLE DEL CAUCA", "CARTAGO", "VALLE DEL CAUCA"),
        ("EL BANCO-MAGDALENA", "EL BANCO", "MAGDALENA"),
        ("LA DORADA-CALDAS", "LA DORADA", "CALDAS"),
    ],
)
def test_parse_sicetac_parametrizado(entrada, esperado_municipio, esperado_dpto):
    r = parse_sicetac(entrada)
    assert r["municipio"] == esperado_municipio
    assert r["departamento"] == esperado_dpto


@pytest.mark.parametrize(
    ("entrada", "esperado_municipio", "esperado_dpto"),
    [
        ("MEDELLIN ANTIOQUIA", "MEDELLIN", "ANTIOQUIA"),
        ("BARRANQUILLA ATLANTICO", "BARRANQUILLA", "ATLANTICO"),
        ("BUCARAMANGA SANTANDER", "BUCARAMANGA", "SANTANDER"),
        ("PEREIRA RISARALDA", "PEREIRA", "RISARALDA"),
        ("CARTAGENA BOLIVAR", "CARTAGENA", "BOLIVAR"),
        ("RIOHACHA LA GUAJIRA", "RIOHACHA", "LA GUAJIRA"),
        ("SINCELEJO SUCRE", "SINCELEJO", "SUCRE"),
        ("VALLEDUPAR CESAR", "VALLEDUPAR", "CESAR"),
        ("PASTO NARINO", "PASTO", "NARINO"),
        ("IBAGUE TOLIMA", "IBAGUE", "TOLIMA"),
    ],
)
def test_parse_rndc_parametrizado(entrada, esperado_municipio, esperado_dpto):
    r = parse_rndc(entrada)
    assert r["municipio"] == esperado_municipio
    assert r["departamento"] == esperado_dpto
