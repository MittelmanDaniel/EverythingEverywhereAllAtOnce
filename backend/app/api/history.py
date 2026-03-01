import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.collected_data import CollectedData
from app.models.user import User
from app.schemas.cookies import HistorySubmission

router = APIRouter(prefix="/history", tags=["history"])


@router.post("")
async def submit_history(
    req: HistorySubmission,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store browser history entries as collected data."""
    collected = CollectedData(
        user_id=user.id,
        service="google",
        data_type="history",
        data_json=json.dumps([e.model_dump() for e in req.entries]),
    )
    db.add(collected)
    await db.commit()

    return {"status": "ok", "entries_stored": len(req.entries)}
