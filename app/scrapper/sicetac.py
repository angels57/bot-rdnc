"""MÃ³dulo para scrapping de SICETAC utilizando Playwright."""

from playwright.async_api import TimeoutError as PlaywrightTimeout

from app.core import get_app_logger
from app.models.sicetac import SicetacParams
from app.scrapper.browser import new_rndc_page
from app.scrapper.decorator import retry_on_timeout
from app.scrapper.selectors import (
    SELECTOR_BT_CALCULAR,
    SELECTOR_CAPTCHA_SICETAC,
    SELECTOR_CARROCERIA_VEHICULO,
    SELECTOR_CONDICION_CARGA,
    SELECTOR_CONFIG_VEHICULO,
    SELECTOR_COSTO_TONELADA,
    SELECTOR_COSTO_TOTAL_VIAJE,
    SELECTOR_DESTINO_VIAJE,
    SELECTOR_HORAS_CARGUE,
    SELECTOR_HORAS_DESCARGUE,
    SELECTOR_ORIGEN_VIAJE,
    SELECTOR_RESULTADO_CAPTCHA,
    SELECTOR_TIPO_CARGA,
    URL_SICETAC,
)
from app.scrapper.utils import sum_detected

logger = get_app_logger("main")


@retry_on_timeout(retries=2, delay=1)
async def abrir_sicetac(page):
    """Abre la pÃ¡gina de SICETAC y espera a que el selector de origen estÃ© disponible."""
    try:
        await page.goto(URL_SICETAC, timeout=15000)
        await page.wait_for_selector(SELECTOR_ORIGEN_VIAJE, timeout=10000)
    except Exception as e:
        logger.error(f"Error al abrir SICETAC: {e!s}")
        raise


async def ensure_visible(page, selector: str, name: str):
    "Asegura que un selector estÃ© visible en la pÃ¡gina, con manejo de errores y logging."
    try:
        await page.wait_for_timeout(
            1000
        )  # Espera un momento para que la pÃ¡gina cargue elementos dinÃ¡micos
        await page.wait_for_selector(selector, timeout=5000)
    except PlaywrightTimeout:
        logger.error(f"âŒ Timeout esperando selector: {name} -> {selector}")
        raise
    except Exception:
        logger.error(f"âŒ Selector no visible: {name} -> {selector}")
        raise


async def safe_action(description: str, selector: str, action):
    "Realiza una acciÃ³n segura con manejo de errores y logging."
    try:
        logger.info(f"Realizando acciÃ³n: {description} (selector: {selector})")
        return await action()
    except Exception as e:
        logger.error(f"âŒ Error en: {description}")
        logger.error(f"Selector: {selector}")
        logger.error(f"Detalle: {e!s}")
        raise


async def retryable_action(page, selector: str, name: str, action, retries=2, delay=1):
    "Realiza una acciÃ³n con reintentos en caso de timeout."
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"ðŸ” Intento {attempt}/{retries} â†’ {name}")

            # 1. Validar que el selector exite
            await ensure_visible(page, selector, name)

            # 2. Ejecutar la acciÃ³n segura
            result = await safe_action(name, selector, action)

            # 3. validacion opcional post accion
            return result

        except Exception as e:
            last_error = e

            logger.warning(
                f"âš ï¸ Fallo en intento {attempt} â†’ {name} ({selector}) | Error: {e}"
            )

            if attempt < retries:
                await page.wait_for_timeout(int(delay * 1000))

            else:
                logger.error(
                    f"âŒ FALLA DEFINITIVA en {name} despuÃ©s de {retries} intentos"
                )
                raise last_error


async def playwright_sicetac(params: SicetacParams) -> dict | bool:
    """FunciÃ³n placeholder para el scrapper de SICETAC."""
    logger.info("playwright_sicetac aÃºn no implementado.")

    # options_path = Path("data/sicetac_combinaciones.json")
    # if not options_path.exists():
    # await export_sicetac_combinaciones(options_path)

    playwright, browser, context, page = await new_rndc_page()
    try:
        await abrir_sicetac(page)
        logger.info(f"Navegando a: {URL_SICETAC}")

        # =--- CONFIGURACION VEHICULO ---

        await retryable_action(
            page,
            SELECTOR_CONFIG_VEHICULO,
            "Selector de configuraciÃ³n de vehÃ­culo",
            lambda: page.locator(SELECTOR_CONFIG_VEHICULO).select_option(
                params.configuracion
            ),
        )

        # =--- CONDICION DE CARGA ---

        await retryable_action(
            page,
            SELECTOR_CONDICION_CARGA,
            "Selector de condiciÃ³n de carga (reintento)",
            lambda: page.locator(SELECTOR_CONDICION_CARGA).select_option(
                params.condicion_carga
            ),
        )

        # =--- CARROCERIA VEHICULO ---
        await retryable_action(
            page,
            SELECTOR_CARROCERIA_VEHICULO,
            "Selector de carrocerÃ­a",
            lambda: page.locator(SELECTOR_CARROCERIA_VEHICULO).select_option(
                params.carroceria
            ),
        )

        if params.condicion_carga == "CARGADO":
            # =--- TIPO DE CARGA ---
            await retryable_action(
                page,
                SELECTOR_TIPO_CARGA,
                "Selector de tipo de carga",
                lambda: page.locator(SELECTOR_TIPO_CARGA).select_option(
                    params.tipo_carga
                ),
            )

        # =--- ORIGEN ---
        await retryable_action(
            page,
            SELECTOR_ORIGEN_VIAJE,
            "Selector de origen (reintento)",
            lambda: page.locator(SELECTOR_ORIGEN_VIAJE).select_option(params.origen),
        )

        # =--- DESTINO ----
        await retryable_action(
            page,
            SELECTOR_DESTINO_VIAJE,
            "Selector de destino (reintento)",
            lambda: page.locator(SELECTOR_DESTINO_VIAJE).select_option(params.destino),
        )

        # =--- HORAS DE CARGUE Y DESCARGUE ---
        await retryable_action(
            page,
            SELECTOR_HORAS_CARGUE,
            "Selector de horas de carga",
            lambda: page.locator(SELECTOR_HORAS_CARGUE).fill(
                params.horas_cargue_descargue
            ),
        )

        # =--- HORAS DE DESCARGUE ---

        await retryable_action(
            page,
            SELECTOR_HORAS_DESCARGUE,
            "Selector de horas de descarga",
            lambda: page.locator(SELECTOR_HORAS_DESCARGUE).fill(
                params.horas_cargue_descargue
            ),
        )

        # =--- CAPTCHA ---
        await retryable_action(
            page,
            SELECTOR_CAPTCHA_SICETAC,
            "Selector de captcha",
            lambda: page.locator(SELECTOR_CAPTCHA_SICETAC).text_content(),
        )
        capcha_text = await safe_action(
            "Obtener texto del captcha",
            SELECTOR_CAPTCHA_SICETAC,
            lambda: page.locator(SELECTOR_CAPTCHA_SICETAC).text_content(),
        )
        sum_captcha = sum_detected(str(capcha_text))

        # =--- RESULTADO CAPTCHA ---
        await retryable_action(
            page,
            SELECTOR_RESULTADO_CAPTCHA,
            "Selector de resultado de captcha",
            lambda: page.locator(SELECTOR_RESULTADO_CAPTCHA).fill(str(sum_captcha)),
        )

        # =--- CALCULAR ---
        await retryable_action(
            page,
            SELECTOR_BT_CALCULAR,
            "Selector del botÃ³n calcular",
            lambda: page.locator(SELECTOR_BT_CALCULAR).click(),
        )

        await page.wait_for_timeout(2000)

        # =--- OBTENER RESULTADO ---
        costo_total = await retryable_action(
            page,
            SELECTOR_COSTO_TOTAL_VIAJE,
            "Obtener valor del costo total del viaje",
            lambda: page.locator(SELECTOR_COSTO_TOTAL_VIAJE).input_value(),
        )
        logger.warning(f"Valor obtenido de costo total: {costo_total}")

        costo_tonelada = await retryable_action(
            page,
            SELECTOR_COSTO_TONELADA,
            "Obtener valor del costo por tonelada",
            lambda: page.locator(SELECTOR_COSTO_TONELADA).input_value(),
        )
        logger.warning(f"Valor obtenido de costo por tonelada: {costo_tonelada}")
        # Limpiar formato monetario que SICETAC incluye
        costo_total = (
            costo_total.replace("$", "").replace(",", "").strip() if costo_total else ""
        )
        costo_tonelada = (
            costo_tonelada.replace("$", "").replace(",", "").strip()
            if costo_tonelada
            else ""
        )

        return {"costo_total": costo_total, "costo_tonelada": costo_tonelada}
    except Exception as e:
        logger.error(f"Error en playwright_sicetac: {e!s}")
        return False
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()
        logger.info("Navegador cerrado en playwright_sicetac.")
