import logging

from app.agents.base import get_client
from app.agents.schemas.history import BrowserHistoryData

logger = logging.getLogger(__name__)

HISTORY_TASK = """
You are logged into Google via the current browser session. Your job is to collect the user's recent web and search activity from the last 7 days.

1. Go to https://myactivity.google.com/myactivity
   - This is the "Web & App Activity" page.
   - If prompted to verify identity or accept terms, do so.

2. Scroll through the activity feed and collect up to 100 of the most recent entries.
   - For each entry note:
     - title: the page title or search query shown
     - url: the URL if visible (may be truncated — collect what you can see)
     - timestamp: the date and time shown (e.g. "Feb 28, 2026, 3:42 PM")
     - source: the service it came from (e.g. "Google Search", "Chrome", "YouTube", "Google Maps", "Google Play", etc.)
   - Entries are grouped by date. Include entries from as many days as visible (up to 7 days back).
   - Scroll down to load more entries if needed, but stop after ~100 entries or when you pass 7 days ago.

3. If the page shows "No activity" or the user has Web & App Activity turned off, return an empty entries list.

Return all data in the structured format requested.
"""


async def run_history_agent(session_id: str) -> dict:
    """Run the browser history collection agent in an existing authenticated session."""
    client = get_client()
    try:
        result = client.run(
            task=HISTORY_TASK,
            session_id=session_id,
            output_schema=BrowserHistoryData,
        )

        task_result = await result
        logger.info("History agent completed")
        return task_result.output.model_dump() if task_result.output else {}
    finally:
        await client.close()
