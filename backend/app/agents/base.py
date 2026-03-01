import logging

from playwright.async_api import async_playwright

from browser_use_sdk.v2 import AsyncBrowserUse as V2Client

from app.config import settings

logger = logging.getLogger(__name__)


def get_client() -> V2Client:
    """v2 client — used for both browser creation and running agent tasks."""
    return V2Client(api_key=settings.browser_use_api_key)


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


async def create_session_with_cookies(cookies: list[dict]) -> str:
    """Create a profile, inject cookies via a standalone browser, then create
    an agent session backed by that profile.

    Returns the agent session ID (usable as sessionId in v2 tasks).
    """
    client = get_client()
    try:
        # 1. Create a profile to persist browser state (cookies, localStorage)
        profile = await client.profiles.create(name="google-cookies")
        profile_id = str(profile.id)
        logger.info(f"Created profile {profile_id}")

        # 2. Create a standalone browser with that profile (gives us CDP URL)
        browser_session = await client.browsers.create(profile_id=profile_id)
        cdp_url = browser_session.cdp_url

        if not cdp_url:
            logger.warning("No CDP URL returned — cookies cannot be injected")
        else:
            # 3. Inject cookies via CDP
            formatted = cookies_to_playwright_format(cookies)
            logger.info(f"Injecting {len(formatted)} cookies via CDP")

            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                await context.add_cookies(formatted)

            logger.info("Cookie injection complete")

        # 4. Stop the standalone browser (saves state back to profile)
        await client.browsers.stop(str(browser_session.id))
        logger.info("Standalone browser stopped, cookies saved to profile")

        # 5. Create an agent session using the same profile
        session = await client.sessions.create(profile_id=profile_id)
        session_id = str(session.id)
        logger.info(f"Created agent session {session_id} with profile {profile_id}")
        return session_id
    finally:
        await client.close()
