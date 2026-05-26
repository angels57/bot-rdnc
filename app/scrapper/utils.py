"Utilidades para el scrapper de RNDC."

import asyncio
import contextlib
import json
import re
from datetime import date
from pathlib import Path

from app.core import get_app_logger
from app.scrapper.browser import new_rndc_page

logger = get_app_logger("utils")


def sum_detected(text: str) -> int:
    """Detecta y suma los números presentes en el texto dado.
    Args:
        text (str): El texto del cual se extraerán los números."""
    nums = re.findall(r"-?\d+", text)

    logger.info(f"Números detectados para el captcha: {nums}")

    return sum(int(n) for n in nums)


def previous_month_year(today: date | None = None) -> str:
    """Calcula el año y mes anterior al mes actual en formato 'AAAAMM'."""
    today = today or date.today()
    # Si el mes actual es enero, el mes anterior es diciembre del año anterior
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1
    return f"{year:04d}{month:02d}"


async def export_sicetac_combinaciones(
    output_path: Path,
    SELECTOR_ORIGEN_VIAJE: str,
    SELECTOR_DESTINO_VIAJE: str,
    URL_SICETAC: str,
) -> dict[str, list[str]] | None:
    """Exporta combinaciones origen-destino desde SICETAC de forma robusta."""

    # ✅ Recomendado en Windows para evitar errores de asyncio
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore[attr-defined]

    playwright, browser, context, page = await new_rndc_page()

    try:
        # ─────────────────────────────────────────────
        # 1. Cargar página correctamente
        # ─────────────────────────────────────────────
        await page.goto(URL_SICETAC, wait_until="domcontentloaded")

        await page.wait_for_selector(SELECTOR_ORIGEN_VIAJE)
        await page.wait_for_load_state("networkidle")

        # ─────────────────────────────────────────────
        # 2. Obtener orígenes (robusto + sin vacíos)
        # ─────────────────────────────────────────────
        async def obtener_origenes():
            options = page.locator(f"{SELECTOR_ORIGEN_VIAJE} option")

            textos = await options.all_text_contents()

            return [t.strip() for t in textos if t.strip() and t.strip() != ""]

        for _ in range(3):
            try:
                origenes = await obtener_origenes()
                if origenes:
                    break
            except Exception:
                await page.wait_for_load_state("networkidle")
        else:
            raise RuntimeError("No se pudieron obtener orígenes")

        combos: dict[str, list[str]] = {}

        # ─────────────────────────────────────────────
        # 3. Función robusta para esperar destinos
        # ─────────────────────────────────────────────
        async def esperar_destinos():
            await page.wait_for_function(
                f"""
                () => {{
                    const sel = document.querySelector("{SELECTOR_DESTINO_VIAJE}");
                    if (!sel) return false;
                    return sel.options.length > 1;
                }}
                """
            )

        # ─────────────────────────────────────────────
        # 4. Iterar orígenes con manejo de navegación
        # ─────────────────────────────────────────────
        for origen in origenes:
            try:
                # 👉 Selección protegida contra navegación
                try:
                    async with page.expect_navigation(timeout=5000):
                        await page.locator(SELECTOR_ORIGEN_VIAJE).select_option(
                            label=origen
                        )
                except Exception:
                    # 👉 No siempre hay navegación, es normal
                    await page.locator(SELECTOR_ORIGEN_VIAJE).select_option(
                        label=origen
                    )

                # Esperar estabilidad
                await page.wait_for_load_state("networkidle")

                # Esperar que destinos realmente carguen
                await esperar_destinos()

                # ─────────────────────────────────────────────
                # 5. Obtener destinos con retry
                # ─────────────────────────────────────────────
                destinos = []

                for _ in range(3):
                    try:
                        textos = await page.locator(
                            f"{SELECTOR_DESTINO_VIAJE} option"
                        ).all_text_contents()

                        destinos = [
                            t.strip() for t in textos if t.strip() and t.strip() != ""
                        ]

                        # ✅ Validación: evitar listas vacías falsas
                        if destinos:
                            break

                    except Exception:
                        pass

                    await page.wait_for_load_state("networkidle")

                combos[origen] = destinos

            except Exception as e:
                logger.warning(f"[SICETAC] Error con origen '{origen}': {e!s}")
                combos[origen] = []

        # ─────────────────────────────────────────────
        # 6. Guardar resultado
        # ─────────────────────────────────────────────
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(
            json.dumps(combos, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return combos

    except Exception as e:
        logger.error(f"[SICETAC] Error general: {e!s}")
        return None

    finally:
        # ─────────────────────────────────────────────
        # 7. Limpieza completa (CRÍTICO en Windows)
        # ─────────────────────────────────────────────
        for obj in (context, browser):
            with contextlib.suppress(Exception):
                await obj.close()

        with contextlib.suppress(Exception):
            await playwright.stop()
