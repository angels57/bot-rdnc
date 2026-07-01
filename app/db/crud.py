from app.core import get_app_logger
from app.db.session import SessionLocal, engine
from app.models.flete import Base, FleteRegistro

logger = get_app_logger("db_crud")


def init_db():
    """Crea las tablas si no existen."""
    Base.metadata.create_all(engine)
    logger.info("Tablas de base de datos inicializadas")


def guardar_flete(
    cod_vehiculo: str,
    origen: str,
    destino: str,
    tarifa: int,
    tipo_flete: str,
    fuente: str,
    agencia: str,
) -> FleteRegistro:
    """Guarda un registro de flete en la base de datos."""
    with SessionLocal() as session:
        db_flete = FleteRegistro(
            cod_vehiculo=cod_vehiculo,
            origen=origen,
            destino=destino,
            tarifa=tarifa,
            tipo_flete=tipo_flete,
            fuente=fuente,
            agencia=agencia,
        )
        session.add(db_flete)
        session.commit()
        session.refresh(db_flete)
        logger.info(f"Flete registrado: {origen} → {destino} (${tarifa:,.0f})")
        return db_flete


def obtener_ultimos_registros(limite: int = 5) -> list[FleteRegistro]:
    """Obtiene los últimos registros de fletes guardados."""
    try:
        with SessionLocal() as session:
            return (
                session.query(FleteRegistro)
                .order_by(FleteRegistro.creado_en.desc())
                .limit(limite)
                .all()
            )
    except Exception as e:
        logger.error(f"Error obteniendo últimos registros: {e}")
        return []
