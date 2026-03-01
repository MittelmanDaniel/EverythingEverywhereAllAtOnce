import logging

from app.agents.base import create_browser_with_cookies, get_client
from app.agents.schemas.google import GoogleData

logger = logging.getLogger(__name__)

GOOGLE_TASK = """
You are logged into Google via cookies. Visit the following Google services and collect data.

1. Go to https://drive.google.com
   - Collect the first 50 most recent files visible in "My Drive" or "Recent".
   - For each file note: name, type (document/spreadsheet/presentation/folder/pdf/etc),
     last modified date, created date (if visible), owner name, whether it is shared,
     and when you last opened it (if visible).

2. Go to https://docs.google.com
   - Collect recent documents shown on the docs homepage (up to 50).
   - For each doc note: title, last edited date, word count (if visible),
     created date (if visible), and number of people it's shared with (if visible).

3. Go to https://mail.google.com
   - Go to the Drafts folder and collect all draft emails (up to 50).
   - For each draft note: subject line, a short snippet of the body, and created/saved date.
   - Also collect the list of labels/folders in the sidebar with their message counts
     and unread counts if visible.

Return all data in the structured format requested.
"""


async def run_google_agent(cookies: list[dict]) -> dict:
    client = get_client()
    try:
        session_id = await create_browser_with_cookies(client, cookies)

        result = client.run(
            task=GOOGLE_TASK,
            session_id=session_id,
            schema=GoogleData,
            start_url="https://drive.google.com",
            allowed_domains=[
                "google.com",
                "drive.google.com",
                "docs.google.com",
                "mail.google.com",
                "accounts.google.com",
            ],
        )

        task_result = await result
        logger.info("Google agent completed")
        return task_result.output.model_dump() if task_result.output else {}
    finally:
        await client.close()
