import logging

from app.agents.base import cookies_to_browser_use_format, get_client
from app.agents.schemas.youtube import YouTubeData

logger = logging.getLogger(__name__)

YOUTUBE_TASK = """
Go to youtube.com. You should already be logged in via cookies.

1. Go to your Library page (youtube.com/feed/library or click Library in sidebar).
2. Collect all your playlists: title, number of videos, last updated date (if visible),
   and whether it's the "Watch Later" playlist.
3. Go to your Subscriptions page (youtube.com/feed/channels).
4. Collect your subscriptions (first 50): channel name, category/topic, and last upload date
   if visible.

Return all data in the structured format requested.
"""


async def run_youtube_agent(cookies: list[dict]) -> dict:
    client = get_client()
    try:
        session = await client.sessions.create(proxy_country_code="us")
        session_id = str(session.id)

        result = await client.run(
            task=YOUTUBE_TASK,
            session_id=session_id,
            output_schema=YouTubeData,
            model="bu-max",
            max_cost_usd=0.50,
        )

        logger.info(f"YouTube agent completed. Cost: {result.total_cost_usd}")
        return result.output.model_dump() if result.output else {}
    finally:
        await client.close()
