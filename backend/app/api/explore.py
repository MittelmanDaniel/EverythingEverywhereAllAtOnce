from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analysis import PathNotTaken
from app.models.user import User

router = APIRouter(prefix="/explore", tags=["explore"])


@router.get("")
async def list_multiverses(db: AsyncSession = Depends(get_db)):
    """Return all users who have PathNotTaken records (public, no auth)."""
    # Subquery: per-user verse count and a sample title
    stmt = (
        select(
            PathNotTaken.user_id,
            func.count(PathNotTaken.id).label("verse_count"),
            func.min(PathNotTaken.title).label("sample_title"),
        )
        .group_by(PathNotTaken.user_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {"users": []}

    # Fetch user emails for display names
    user_ids = [r.user_id for r in rows]
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_by_id = {u.id: u for u in users_result.scalars().all()}

    users = []
    for r in rows:
        user = users_by_id.get(r.user_id)
        display_name = user.email.split("@")[0] if user else "unknown"
        users.append({
            "user_id": r.user_id,
            "display_name": display_name,
            "verse_count": r.verse_count,
            "sample_title": r.sample_title,
        })

    return {"users": users}
