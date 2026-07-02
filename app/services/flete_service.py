"""Servicio para consultar registros de fletes desde la base de datos."""

from app.core import get_app_logger
from app.db.session import get_session_factory
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
    logger.info(
        f"Consultando fletes registrados para: origen='{origen}', "
        f"destino='{destino}', config='{configuracion}'"
    )

    try:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            query = session.query(FleteRegistro).filter(
                FleteRegistro.origen.ilike(f"%{origen}%"),
                FleteRegistro.destino.ilike(f"%{destino}%"),
            )

            if configuracion:
                query = query.filter(FleteRegistro.cod_vehiculo == configuracion)

            registros = query.order_by(FleteRegistro.creado_en.desc()).limit(10).all()

            if registros:
                logger.info(
                    f"Se encontraron {len(registros)} registros de flete previos"
                )
            else:
                logger.info(
                    "No se encontraron fletes registrados para esta combinación"
                )

            return [r.dict() for r in registros]
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error consultando fletes registrados: {e}")
        return []
