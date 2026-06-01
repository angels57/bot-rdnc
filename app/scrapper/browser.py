"""Crea una nueva página de Playwright para interactuar con el sitio web de RNDC."""

from playwright.async_api import async_playwright


async def new_rndc_page():
    """Crea una nueva página de Playwright para interactuar con el sitio web de RNDC."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True, channel="chrome", timeout=30000
    )
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()
    return playwright, browser, context, page
