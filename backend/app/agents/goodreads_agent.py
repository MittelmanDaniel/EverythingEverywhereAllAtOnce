import logging

from app.agents.base import cookies_to_browser_use_format, get_client
from app.agents.schemas.goodreads import GoodreadsData

logger = logging.getLogger(__name__)

GOODREADS_TASK = """
Go to goodreads.com. You should already be logged in via cookies.

1. Go to "My Books" page (goodreads.com/review/list).
2. Collect books from all shelves (read, currently-reading, to-read):
   title, author, shelf name, date added, your rating (if any), page count.
   Page through results if there are multiple pages. Get at least the first 50 books.
3. Check if there's a reading challenge for the current year:
   goal number and current progress.
4. Note the total books read count.

Return all data in the structured format requested.
"""


async def run_goodreads_agent(cookies: list[dict]) -> dict:
    client = get_client()
    try:
        session = await client.sessions.create(proxy_country_code="us")
        session_id = str(session.id)

        result = await client.run(
            task=GOODREADS_TASK,
            session_id=session_id,
            output_schema=GoodreadsData,
            model="bu-max",
            max_cost_usd=0.50,
        )

        logger.info(f"Goodreads agent completed. Cost: {result.total_cost_usd}")
        return result.output.model_dump() if result.output else {}
    finally:
        await client.close()
