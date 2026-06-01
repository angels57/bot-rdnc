"""Scraper para descargar datos estadísticos de RNDC."""

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
        await page.wait_for_timeout(
            6000
        )  # Esperar un momento para asegurarse de que la descarga se inicie

        # Guardar archivo descargado
        download = await download_info.value
        await download.save_as("data/RNDC.xlsx")
        logger.info("✅ Archivo descargado exitosamente en data/RNDC.xlsx")

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
