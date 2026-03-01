from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.analysis import PathNotTaken
from app.models.connection import ServiceConnection
from app.models.user import User
from app.schemas.analysis import AnalysisResponse, PathNotTakenResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("", response_model=AnalysisResponse)
async def get_analysis(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check overall status
    conns_result = await db.execute(
        select(ServiceConnection).where(ServiceConnection.user_id == user.id)
    )
    conns = conns_result.scalars().all()

    if not conns:
        status = "pending"
    elif any(c.status == "collecting" for c in conns):
        status = "collecting"
    else:
        status = "ready"

    # Get analysis results
    paths_result = await db.execute(
        select(PathNotTaken)
        .where(PathNotTaken.user_id == user.id)
        .order_by(PathNotTaken.timeline_date.desc().nullslast())
    )
    paths = paths_result.scalars().all()

    return AnalysisResponse(
        paths=[
            PathNotTakenResponse(
                id=p.id,
                category=p.category,
                title=p.title,
                description=p.description,
                evidence_json=p.evidence_json,
                source_service=p.source_service,
                confidence=p.confidence,
                timeline_date=p.timeline_date,
            )
            for p in paths
        ],
        status=status,
    )


@router.post("/refresh")
async def refresh_analysis(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.analysis_service import run_analysis

    background_tasks.add_task(run_analysis, user.id)
    return {"status": "analyzing"}
