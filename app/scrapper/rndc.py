"""Scraper para descargar datos estadísticos de RNDC."""

from pathlib import Path

from app.core.logging import get_app_logger
from app.scrapper.browser import new_rndc_page
from app.scrapper.selectors import (
    SELECTOR_BT_ESTADISTICAS,
    SELECTOR_CAPTCHA,
    SELECTOR_FECHA_INICIAL,
    SELECTOR_RESULTADO,
    URL,
)
from app.scrapper.utils import previous_month_year, sum_detected

logger = get_app_logger("rndc")


async def playwright_rndc():
    """Descarga datos estadísticos del sitio web de RNDC."""
    logger.info("Iniciando Playwright para descargar datos de RNDC...")
    playwright, browser, context, page = await new_rndc_page()

    try:
        await page.goto(URL)
        logger.info(f"Navegando a: {URL}")

        # Esperar que cargue el elemento de captcha
        await page.wait_for_selector(SELECTOR_CAPTCHA)
        sum_text = await page.locator(SELECTOR_CAPTCHA).text_content()
        sum_verify = sum_detected(str(sum_text))
        logger.info(f"Captcha resuelto: {sum_verify}")

        # Rellenar el resultado del captcha
        await page.fill(SELECTOR_RESULTADO, str(sum_verify))
        logger.info("Resultado del captcha ingresado")

        # Calcular y rellenar la fecha del mes anterior
        year_month = previous_month_year()
        await page.fill(SELECTOR_FECHA_INICIAL, year_month)
        logger.info(f"Fecha ingresada: {year_month}")

        # Iniciar descarga
        async with page.expect_download() as download_info:
            logger.info("Haciendo clic en el botón de descargar...")
            await page.locator(SELECTOR_BT_ESTADISTICAS).click()

        # Guardar archivo descargado
        download = await download_info.value
        dest = Path("data/RNDC.xlsx")
        await download.save_as(dest)

        # ✅ Validar que el archivo no esté vacío ni sea una respuesta HTML de error
        if not dest.exists() or dest.stat().st_size == 0:
            logger.error("❌ Descarga completada pero el archivo está vacío.")
            return False

        # Los archivos XLSX válidos comienzan con la firma PK (ZIP)
        with dest.open("rb") as f:
            magic = f.read(4)
        if magic != b"PK\x03\x04":
            logger.error(
                f"❌ El archivo descargado no es un XLSX válido (firma: {magic!r}). "
                "Probablemente el servidor devolvio una página HTML de error."
            )
            dest.unlink(missing_ok=True)  # Eliminar archivo corrupto
            return False

        logger.info(f"✅ Archivo descargado y validado exitosamente en {dest}")

        await page.wait_for_timeout(2000)

    except Exception as e:
        logger.error(f"❌ Error durante la ejecución de Playwright: {e!s}")
        return False

    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
        logger.info("Navegador cerrado")

    return True
