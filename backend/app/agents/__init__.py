from app.agents.github_agent import run_github_agent
from app.agents.goodreads_agent import run_goodreads_agent
from app.agents.youtube_agent import run_youtube_agent

AGENTS = {
    "github": run_github_agent,
    "youtube": run_youtube_agent,
    "goodreads": run_goodreads_agent,
}


async def run_agent(service: str, cookies: list[dict]) -> dict:
    agent_fn = AGENTS.get(service)
    if not agent_fn:
        raise ValueError(f"No agent for service: {service}")
    return await agent_fn(cookies)
