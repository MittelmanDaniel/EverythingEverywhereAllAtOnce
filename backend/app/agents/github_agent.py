import logging

from app.agents.base import cookies_to_browser_use_format, get_client
from app.agents.schemas.github import GitHubData

logger = logging.getLogger(__name__)

GITHUB_TASK = """
Go to github.com. You should already be logged in via cookies.

1. Find the logged-in username from the profile menu or navigation.
2. Go to your repositories page (click "Your repositories" or go to github.com/{username}?tab=repositories).
3. For ALL your repositories, collect: name, description, primary language, star count,
   last commit date, whether it's a fork, and whether it has any commits in the last 6 months.
   Page through all repos if there are multiple pages.
4. Go to your stars page (github.com/{username}?tab=stars).
5. Collect your first 50 starred repos: repo name, owner, description, and topic tags.
6. Go back to your profile and note:
   - Your bio text
   - Which years show contributions on the contribution graph

Return all data in the structured format requested.
"""


async def run_github_agent(cookies: list[dict]) -> dict:
    client = get_client()
    try:
        # Create a session with cookies pre-loaded
        session = await client.sessions.create(proxy_country_code="us")
        session_id = str(session.id)

        # Run the agent
        result = await client.run(
            task=GITHUB_TASK,
            session_id=session_id,
            output_schema=GitHubData,
            model="bu-max",
            max_cost_usd=0.50,
        )

        logger.info(f"GitHub agent completed. Cost: {result.total_cost_usd}")
        return result.output.model_dump() if result.output else {}
    finally:
        await client.close()
