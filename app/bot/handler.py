import asyncio
import json
from pathlib import Path

import polars as pl

from app.core import get_app_logger, sicetac_cache
from app.data import cargar_data, processor
from app.models.sicetac import SicetacParams
from app.nlp.normalizer import normalizar_sicetac_a_rndc
from app.scrapper import playwright_sicetac
from app.services import consultar_ruta

PATH_FILE = Path("data/RNDC.xlsx")
PATH_LOOKUP = Path("data/sicetac_to_rndc.json")

logger = get_app_logger("bot_handler")


class BotHandler:
    def __init__(self):
        df_raw = cargar_data(PATH_FILE)
        self.df = processor(df_raw)
        self.origenes = self.df["MUNICIPIOORIGEN"].unique()
        self.destinos = self.df["MUNICIPIODESTINO"].unique()
        self.municipios = (
            pl.concat([self.origenes, self.destinos]).unique().unique().to_list()
        )

        # Cargar el lookup table de normalización
        if PATH_LOOKUP.exists():
            try:
                with PATH_LOOKUP.open("r", encoding="utf-8") as f:
                    self.lookup = json.load(f)
                logger.info(
                    f"💾 Lookup table de normalización cargado exitosamente ({len(self.lookup)} entradas)"
                )
            except Exception as e:
                logger.error(f"Error al cargar el lookup table: {e!s}")
                self.lookup = {}
        else:
            logger.warning(
                f"⚠️ No se encontró el lookup table en {PATH_LOOKUP}. Se utilizará fallback fuzzy completo."
            )
            self.lookup = {}

    def _run_scrapping(
        self,
        params: SicetacParams,
    ):
        # Generar una clave única para la consulta normalizada
        key_parts = [
            params.origen.strip().lower(),
            params.destino.strip().lower(),
            params.configuracion.strip().lower(),
            params.condicion_carga.strip().lower(),
            params.carroceria.strip().lower(),
            params.tipo_carga.strip().lower(),
            params.horas_cargue_descargue.strip().lower(),
        ]
        cache_key = ":".join(key_parts)

        # Intentar obtener de la caché persistente
        try:
            cached_val = sicetac_cache.get(cache_key)
            if cached_val:
                logger.info(
                    f"Caché HIT para ruta: {params.origen} -> {params.destino} | Valor recuperado: {cached_val}"
                )
                return cached_val
        except Exception as e:
            logger.warning(f"Error al leer del caché persistente: {e!s}")

        logger.info(
            f"Caché MISS. Ejecutando scrapping real con: Origen='{params.origen}', Destino='{params.destino}', Configuración='{params.configuracion}', Condición de Carga='{params.condicion_carga}', Carrocería='{params.carroceria}', Tipo de Carga='{params.tipo_carga} ', Horas Cargue/Descargue='{params.horas_cargue_descargue}'"
        )
        try:
            costo = asyncio.run(playwright_sicetac(params))
            if costo:
                try:
                    # Almacenar en caché persistente durante 7 días (604800 segundos)
                    sicetac_cache.set(cache_key, costo, expire=604800)
                    logger.info(
                        f"Guardado en caché persistente: {cache_key} -> {costo}"
                    )
                except Exception as e:
                    logger.warning(f"Error al escribir en el caché persistente: {e!s}")
            return costo
        except Exception as e:
            logger.error(f"Error ejecutando playwright_sicetac: {e!s}")
            return False

    def run(
        self,
        params: SicetacParams,
    ) -> dict:
        logger.info(
            "Iniciando proceso de consulta de ruta con los siguientes parámetros:"
        )
        # Normalizar los nombres de origen y destino usando la lista combinada de municipios y el lookup table
        origen_df = normalizar_sicetac_a_rndc(
            params.origen, self.municipios, self.lookup
        )
        destino_df = normalizar_sicetac_a_rndc(
            params.destino, self.municipios, self.lookup
        )

        if not origen_df or not destino_df:
            raise ValueError(
                "No pude identificar las ciudades de origen y destino. "
                "Selecciona ambos campos antes de continuar."
            )

        costo = self._run_scrapping(params)

        return {
            "origen": params.origen,
            "destino": params.destino,
            "configuracion": params.configuracion,
            "costo_sicetac": costo,
            "ruta_db": consultar_ruta(
                self.df,
                origen=origen_df,
                destino=destino_df,
                configuracion=params.configuracion,
            ),
        }
