from app.core import get_app_logger
from app.db.session import get_engine, get_session_factory
from app.models.flete import Base, FleteRegistro

logger = get_app_logger("db_crud")


def init_db() -> bool:
    """Crea las tablas si no existen."""
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Tablas de base de datos inicializadas")
        return True
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
        return False


def guardar_flete(
    cod_vehiculo: str,
    origen: str,
    destino: str,
    tarifa: int,
    tipo_flete: str,
    fuente: str,
    agencia: str,
) -> FleteRegistro | None:
    """Guarda un registro de flete en la base de datos."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
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
    except Exception as e:
        session.rollback()
        logger.error(f"Error guardando flete: {e}")
        return None
    finally:
        session.close()


def obtener_ultimos_registros(limite: int = 10) -> list[FleteRegistro]:
    """Obtiene los últimos registros únicos por COD+origen+destino."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        registros = (
            session.query(FleteRegistro)
            .order_by(FleteRegistro.creado_en.desc())
            .limit(50)
            .all()
        )
        vistos = set()
        unicos = []
        for r in registros:
            key = (r.cod_vehiculo, r.origen, r.destino)
            if key not in vistos:
                vistos.add(key)
                unicos.append(r)
                if len(unicos) >= limite:
                    break
        return unicos
    except Exception as e:
        logger.error(f"Error obteniendo últimos registros: {e}")
        return []
    finally:
        session.close()
