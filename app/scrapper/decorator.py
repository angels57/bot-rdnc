import asyncio
from functools import wraps

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.core.logging import get_app_logger

logger = get_app_logger("Decorator")


def retry_on_timeout(retries=3, delay=2):
    """Decorador para reintentar una función asíncrona en caso de timeout de Playwright."""

    def decorator(func):  # Decorador para manejar reintentos
        @wraps(func)  # Preservar metadata de la función original
        async def wrapper(*args, **kwargs):
            for intento in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)  # Intentar ejecutar la función
                except PlaywrightTimeoutError as exc:
                    last_exception = exc  # Guardar la última excepción para reportar si se agotan los intentos
                    logger.warning(
                        f"Intento {intento} de {retries} fallido por timeout: {exc!s}"
                    )
                    if intento < retries:
                        logger.info(f"Reintentando en {delay} segundos...")
                        await asyncio.sleep(delay)  # Esperar antes de reintentar

            raise last_exception  # Si se agotan los intentos, lanzar la última excepción

        return wrapper

    return decorator
