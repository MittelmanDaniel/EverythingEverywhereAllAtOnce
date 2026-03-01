from app.agents.google_agent import run_google_agent

AGENTS = {
    "google": run_google_agent,
}


async def run_agent(service: str, cookies: list[dict]) -> dict:
    agent_fn = AGENTS.get(service)
    if not agent_fn:
        raise ValueError(f"No agent for service: {service}")
    return await agent_fn(cookies)
