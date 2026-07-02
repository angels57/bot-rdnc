from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.core import get_app_logger

logger = get_app_logger("db_session")

_engine = None
_SessionLocal = None


def init_engine() -> None:
    """Inicializa engine y session factory de forma perezosa."""
    global _engine, _SessionLocal
    if _engine is not None:
        return

    db_url = settings.DATABASE_URL_REGISTER
    if not db_url:
        logger.error("DATABASE_URL_REGISTER no está configurada en .env")
        raise ValueError("DATABASE_URL_REGISTER no está configurada en .env")

    logger.info(
        f"Conectando a base de datos de registros: "
        f"{db_url.split('@')[-1] if '@' in db_url else db_url}"
    )

    _engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    logger.info("Engine de base de datos inicializado correctamente")


def get_engine():
    """Retorna el engine, inicializándolo si es necesario."""
    init_engine()
    return _engine


def get_session_factory():
    """Retorna la fábrica de sesiones, inicializándola si es necesario."""
    init_engine()
    return _SessionLocal
