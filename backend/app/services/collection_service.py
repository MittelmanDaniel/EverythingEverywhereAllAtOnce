import json
import logging
from datetime import datetime

from sqlalchemy import select

from app.database import async_session
from app.models.collected_data import CollectedData
from app.models.connection import ServiceConnection
from app.services.analysis_service import run_analysis

logger = logging.getLogger(__name__)


async def run_collection(user_id: str, service: str, session_id: str):
    """Background task: run Browser Use agent to collect data from a service."""
    async with async_session() as db:
        try:
            result = await db.execute(
                select(ServiceConnection).where(
                    ServiceConnection.user_id == user_id,
                    ServiceConnection.service == service,
                )
            )
            conn = result.scalar_one_or_none()
            if not conn:
                return

            from app.agents import run_agent

            agent_result = await run_agent(service, session_id)

            collected = CollectedData(
                user_id=user_id,
                service=service,
                data_type="full",
                data_json=json.dumps(agent_result),
            )
            db.add(collected)

            conn.status = "collected"
            conn.last_collected_at = datetime.utcnow()
            await db.commit()

            # Auto-trigger analysis after collection
            await run_analysis(user_id)

        except Exception as e:
            logger.error(f"Collection failed for {user_id}/{service}: {e}")
            conn.status = "error"
            await db.commit()
