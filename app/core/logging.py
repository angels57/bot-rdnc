"""Configuración de logging para la aplicación."""

import json
import logging
import os

from rich.logging import RichHandler


class JSONFormatter(logging.Formatter):
    """Formateador de logs en formato JSON."""

    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record)


def get_app_logger(
    name: str = "app",
    level: str = "DEBUG",
    log_file: str = "logs/app.json",
) -> logging.Logger:
    """Obtiene el logger de la aplicación."""

    # Crear carpeta de logs si no existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        # Formateador para CONSOLA (Humano)
        console_fmt = logging.Formatter(" %(module)s | %(funcName)s | %(message)s")
        console_handler = RichHandler(rich_tracebacks=True, markup=True)
        console_handler.setFormatter(console_fmt)

        # Formateador para ARCHIVO (JSON / Máquina)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())

        # Añadir ambos al logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
