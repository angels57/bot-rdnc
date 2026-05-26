"""Crea una nueva página de Playwright para interactuar con el sitio web de RNDC."""

import os

from playwright.async_api import async_playwright


async def new_rndc_page():
    """Crea una nueva página de Playwright para interactuar con el sitio web de RNDC.

    El modo headless es configurable mediante la variable de entorno HEADLESS.
    Por defecto es True (sin ventana visual) para ser compatible con servidores sin display.
    Para desarrollo local con ventana visual, usa: HEADLESS=false
    """
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=headless,
        channel="chrome",
        timeout=30000,
    )
    context = await browser.new_context(
        accept_downloads=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()
    return playwright, browser, context, page
