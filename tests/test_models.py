"""Tests para app/models/sicetac.py — validación del modelo SicetacParams."""

import pytest
from pydantic import ValidationError

from app.models.sicetac import SicetacParams

# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────


@pytest.fixture
def params_validos():
    return {
        "origen": "MEDELLIN - MEDELLIN - ANTIOQUIA",
        "destino": "BOGOTA DISTRITO CAPITAL - BOGOTA D. C.",
        "configuracion": "C3S3",
        "condicion_carga": "cargado",
        "carroceria": "estacas",
        "tipo_carga": "general",
        "horas_cargue_descargue": "1",
    }


# ─────────────────────────────────────────────
# Tests de SicetacParams
# ─────────────────────────────────────────────


class TestSicetacParams:
    def test_crea_instancia_valida(self, params_validos):
        p = SicetacParams(**params_validos)
        assert p.origen == "MEDELLIN - MEDELLIN - ANTIOQUIA"
        assert p.destino == "BOGOTA DISTRITO CAPITAL - BOGOTA D. C."
        assert p.configuracion == "C3S3"

    def test_todos_los_campos_son_str(self, params_validos):
        p = SicetacParams(**params_validos)
        assert isinstance(p.origen, str)
        assert isinstance(p.destino, str)
        assert isinstance(p.configuracion, str)
        assert isinstance(p.condicion_carga, str)
        assert isinstance(p.carroceria, str)
        assert isinstance(p.tipo_carga, str)
        assert isinstance(p.horas_cargue_descargue, str)

    def test_campo_origen_requerido(self, params_validos):
        del params_validos["origen"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_campo_destino_requerido(self, params_validos):
        del params_validos["destino"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_campo_configuracion_requerido(self, params_validos):
        del params_validos["configuracion"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_campo_condicion_carga_requerido(self, params_validos):
        del params_validos["condicion_carga"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_campo_carroceria_requerido(self, params_validos):
        del params_validos["carroceria"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_campo_tipo_carga_requerido(self, params_validos):
        del params_validos["tipo_carga"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_campo_horas_requerido(self, params_validos):
        del params_validos["horas_cargue_descargue"]
        with pytest.raises(ValidationError):
            SicetacParams(**params_validos)

    def test_admite_strings_vacios(self, params_validos):
        # Pydantic BaseModel por defecto acepta strings vacíos
        params_validos["origen"] = ""
        p = SicetacParams(**params_validos)
        assert p.origen == ""

    def test_serializa_a_dict(self, params_validos):
        p = SicetacParams(**params_validos)
        d = p.model_dump()
        assert isinstance(d, dict)
        assert set(d.keys()) == {
            "origen",
            "destino",
            "configuracion",
            "condicion_carga",
            "carroceria",
            "tipo_carga",
            "horas_cargue_descargue",
        }

    def test_serializa_a_json(self, params_validos):
        p = SicetacParams(**params_validos)
        json_str = p.model_dump_json()
        assert isinstance(json_str, str)
        assert "origen" in json_str

    def test_igualdad_por_valor(self, params_validos):
        p1 = SicetacParams(**params_validos)
        p2 = SicetacParams(**params_validos)
        assert p1 == p2

    def test_valores_distintos_no_son_iguales(self, params_validos):
        p1 = SicetacParams(**params_validos)
        params_validos["origen"] = "CALI"
        p2 = SicetacParams(**params_validos)
        assert p1 != p2
