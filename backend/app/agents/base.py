import logging

from browser_use_sdk.v2 import AsyncBrowserUse as V2Client

from app.config import settings

logger = logging.getLogger(__name__)


def get_client() -> V2Client:
    """v2 client — used for both session management and running agent tasks."""
    return V2Client(api_key=settings.browser_use_api_key)


async def stop_session(session_id: str) -> None:
    """Stop a Browser Use session to free resources."""
    client = get_client()
    try:
        await client.sessions.stop(session_id)
        logger.info(f"Stopped session {session_id}")
    except Exception as e:
        logger.warning(f"Failed to stop session {session_id}: {e}")
    finally:
        await client.close()


async def create_session(start_url: str = "https://accounts.google.com") -> tuple[str, str | None]:
    """Create a Browser Use session with keep_alive=True.

    Returns (session_id, live_url).
    """
    client = get_client()
    try:
        session = await client.sessions.create(
            keep_alive=True,
            start_url=start_url,
        )
        session_id = str(session.id)
        live_url = session.live_url
        logger.info(f"Created session {session_id}, live_url={live_url}")
        return session_id, live_url
    finally:
        await client.close()
