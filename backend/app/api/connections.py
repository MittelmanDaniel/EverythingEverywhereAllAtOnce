from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import create_session
from app.api.deps import get_current_user
from app.database import get_db
from app.models.connection import ServiceConnection
from app.models.user import User
from app.schemas.connections import ConnectionsResponse, ConnectionStatus

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("", response_model=ConnectionsResponse)
async def list_connections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(ServiceConnection.user_id == user.id)
    )
    conns = result.scalars().all()
    return ConnectionsResponse(
        connections=[
            ConnectionStatus(
                service=c.service,
                status=c.status,
                last_collected_at=c.last_collected_at.isoformat() if c.last_collected_at else None,
            )
            for c in conns
        ]
    )


@router.post("/session/start")
async def start_session(
    user: User = Depends(get_current_user),
):
    """Create a Browser Use session and return the live URL for user login."""
    session_id, live_url = await create_session()
    return {"session_id": session_id, "live_url": live_url}


class CollectRequest(BaseModel):
    session_id: str


@router.post("/{service}/collect")
async def trigger_collection(
    service: str,
    body: CollectRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id,
            ServiceConnection.service == service,
        )
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail=f"No connection for {service}")

    conn.status = "collecting"
    await db.commit()

    from app.services.collection_service import run_collection

    background_tasks.add_task(run_collection, user.id, service, body.session_id)
    return {"status": "collecting", "service": service}


@router.delete("/{service}")
async def delete_connection(
    service: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.user_id == user.id,
            ServiceConnection.service == service,
        )
    )
    conn = result.scalar_one_or_none()
    if conn:
        await db.delete(conn)
        await db.commit()
    return {"status": "ok"}
