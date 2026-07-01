"""Servicio para consultar registros de fletes desde la base de datos."""

from app.core import get_app_logger
from app.db.session import SessionLocal
from app.models.flete import FleteRegistro

logger = get_app_logger("flete_service")


def consultar_fletes_registrados(
    origen: str,
    destino: str,
    configuracion: str | None = None,
) -> list[dict]:
    """Busca registros de flete previos para una ruta específica.

    Args:
        origen: Ciudad de origen
        destino: Ciudad de destino
        configuracion: Código de configuración del vehículo (opcional)

    Returns:
        Lista de diccionarios con los registros encontrados
    """
    try:
        with SessionLocal() as session:
            query = session.query(FleteRegistro).filter(
                FleteRegistro.origen.ilike(f"%{origen}%"),
                FleteRegistro.destino.ilike(f"%{destino}%"),
            )

            if configuracion:
                query = query.filter(FleteRegistro.cod_vehiculo == configuracion)

            registros = query.order_by(FleteRegistro.creado_en.desc()).limit(10).all()
            return [r.dict() for r in registros]

    except Exception as e:
        logger.error(f"Error consultando fletes registrados: {e}")
        return []
