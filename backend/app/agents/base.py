import logging

from browser_use_sdk.v3 import AsyncBrowserUse

from app.config import settings

logger = logging.getLogger(__name__)


def get_client() -> AsyncBrowserUse:
    return AsyncBrowserUse(api_key=settings.browser_use_api_key)


def cookies_to_browser_use_format(cookies: list[dict]) -> list[dict]:
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
            # Playwright expects "Strict", "Lax", or "None"
            same_site = c["sameSite"].capitalize()
            if same_site in ("Strict", "Lax", "None"):
                cookie["sameSite"] = same_site
        if c.get("expirationDate"):
            cookie["expires"] = c["expirationDate"]
        formatted.append(cookie)
    return formatted
