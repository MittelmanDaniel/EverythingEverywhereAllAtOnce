from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.post("/{service}/collect")
async def trigger_collection(
    service: str,
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

    # Import here to avoid circular imports
    from app.services.collection_service import run_collection

    background_tasks.add_task(run_collection, user.id, service)
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
