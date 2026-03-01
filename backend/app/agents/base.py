import logging

from playwright.async_api import async_playwright

from browser_use_sdk.v2 import AsyncBrowserUse as V2Client
from browser_use_sdk.v3 import AsyncBrowserUse as V3Client

from app.config import settings

logger = logging.getLogger(__name__)


def get_v2_client() -> V2Client:
    """v2 client — used for browsers.create() which exposes CDP URLs."""
    return V2Client(api_key=settings.browser_use_api_key)


def get_v3_client() -> V3Client:
    """v3 client — used for running agent tasks."""
    return V3Client(api_key=settings.browser_use_api_key)


def cookies_to_playwright_format(cookies: list[dict]) -> list[dict]:
    """Convert Chrome extension cookie format to Playwright-compatible format."""
    formatted = []
    for c in cookies:
        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
        }
        if c.get("secure"):
            cookie["secure"] = True
        if c.get("httpOnly"):
            cookie["httpOnly"] = True
        if c.get("sameSite"):
            same_site = c["sameSite"].capitalize()
            if same_site in ("Strict", "Lax", "None"):
                cookie["sameSite"] = same_site
        if c.get("expirationDate"):
            cookie["expires"] = c["expirationDate"]
        formatted.append(cookie)
    return formatted


async def create_browser_with_cookies(cookies: list[dict]) -> str:
    """Create a cloud browser via v2, inject cookies via CDP.

    Returns the browser session ID (usable as sessionId in v3 tasks).
    """
    v2 = get_v2_client()
    try:
        browser_session = await v2.browsers.create()
        session_id = str(browser_session.id)
        cdp_url = browser_session.cdp_url

        if not cdp_url:
            logger.warning("No CDP URL returned — cookies cannot be injected")
            return session_id

        formatted = cookies_to_playwright_format(cookies)
        logger.info(f"Injecting {len(formatted)} cookies via CDP into session {session_id}")

        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            await context.add_cookies(formatted)

        logger.info(f"Cookie injection complete for session {session_id}")
        return session_id
    finally:
        await v2.close()
