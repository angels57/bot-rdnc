from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.core import get_app_logger

logger = get_app_logger("db_session")

db_url = settings.DATABASE_URL_REGISTER
if not db_url:
    logger.error("DATABASE_URL_REGISTER no está configurada en .env")
    raise ValueError("DATABASE_URL_REGISTER no está configurada en .env")

logger.info(f"Conectando a base de datos de registros: {db_url.split('@')[-1] if '@' in db_url else db_url}")

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
