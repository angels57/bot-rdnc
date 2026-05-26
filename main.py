"""Módulo principal para ejecutar el bot de scrapping de RDNC y SICETAC."""

import asyncio
import os
from datetime import date

from app.core.logging import get_app_logger
from app.scrapper import playwright_rndc
from app.UI.chat_page import render

logger = get_app_logger("main")


def main():
    render()
    # o ruta no existe, o es el día 1 del mes, o es el día 2 del mes y no se ha descargado el archivo aún
    if date.today().day == 1 or os.path.exists("data/RNDC.xlsx") is False:
        try:
            asyncio.run(playwright_rndc())
        except Exception as e:
            logger.error(f"Error ejecutando playwright_rndc: {e!s}")


if __name__ == "__main__":
    main()
