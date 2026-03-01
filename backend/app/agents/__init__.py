from app.agents.google_agent import run_google_agent
from app.agents.history_agent import run_history_agent

AGENTS = {
    "google": run_google_agent,
    "history": run_history_agent,
}


async def run_agent(service: str, session_id: str) -> dict:
    agent_fn = AGENTS.get(service)
    if not agent_fn:
        raise ValueError(f"No agent for service: {service}")
    return await agent_fn(session_id)
