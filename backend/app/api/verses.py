import hashlib
import json

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.analysis import PathNotTaken
from app.models.user import User
from app.utils.security import decode_access_token

optional_bearer = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/verses", tags=["verses"])

# Category → zone mapping (0=close, 1=adjacent, 2=divergent, 3=far, 4=outer)
CATEGORY_ZONE = {
    "abandoned_project": 1,
    "forgotten_interest": 2,
    "dormant_period": 3,
}

# Zone distance ranges
ZONE_DIST = {
    0: (4, 6),
    1: (8, 12),
    2: (14, 18),
    3: (22, 28),
    4: (35, 45),
}

# Color palettes per category
CATEGORY_COLORS = {
    "abandoned_project": [
        [255, 190, 70],
        [240, 200, 100],
        [255, 160, 30],
    ],
    "forgotten_interest": [
        [60, 200, 255],
        [50, 120, 255],
        [180, 60, 255],
        [220, 50, 220],
    ],
    "dormant_period": [
        [255, 70, 130],
        [255, 80, 40],
        [30, 230, 140],
    ],
}

ZONES = [
    "Close — a version of you that almost happened",
    "Adjacent — a familiar life, tilted",
    "Divergent — you might not recognize yourself",
    "Far reach — barely you anymore",
    "Outer rim — a stranger with your eyes",
]


def _stable_hash(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def path_to_verse(path: PathNotTaken, index: int) -> dict:
    """Transform a PathNotTaken DB record into the verse format for the map."""
    zone = CATEGORY_ZONE.get(path.category, 2)
    dist_min, dist_max = ZONE_DIST[zone]

    # Confidence pushes closer (higher confidence = closer to you)
    confidence = path.confidence or 0.5
    if confidence > 0.75:
        zone = max(0, zone - 1)
        dist_min, dist_max = ZONE_DIST[zone]

    # Stable distance from title hash
    h = _stable_hash(path.id)
    dist = dist_min + (h % 1000) / 1000 * (dist_max - dist_min)

    # Pick color from palette
    colors = CATEGORY_COLORS.get(path.category, [[180, 180, 255]])
    color = colors[h % len(colors)]

    # Parse year/month from timeline_date
    year = ""
    month = ""
    if path.timeline_date:
        parts = path.timeline_date.split("-")
        year = parts[0] if len(parts) >= 1 else ""
        if len(parts) >= 2:
            month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            try:
                month = month_names[int(parts[1])]
            except (ValueError, IndexError):
                month = ""

    # Try to extract a URL from evidence
    url = ""
    try:
        evidence = json.loads(path.evidence_json) if path.evidence_json else {}
        url = evidence.get("domain", evidence.get("url", ""))
        if not url:
            # Try to get it from nested objects
            for key in ("doc", "draft", "file"):
                if key in evidence:
                    url = evidence[key].get("url", evidence[key].get("name", ""))
                    break
    except (json.JSONDecodeError, AttributeError):
        pass

    if not url:
        url = path.title

    zone_label = ZONES[zone]

    return {
        "id": path.id,
        "y": year,
        "mo": month,
        "url": url,
        "t": path.title,
        "w": path.description,
        "c": color,
        "zone": zone,
        "dist": round(dist, 1),
        "a": {
            "l": f"{zone_label.split('—')[0].strip().upper()} VERSE — {path.title.upper()[:40]}",
            "t": path.title,
            "s": path.description[:100] + ("..." if len(path.description) > 100 else ""),
            "cv": path.description,
            "p": (
                f"Write a deeply cinematic 150-word narrative about someone whose digital life reveals: "
                f"\"{path.title}\" — {path.description} "
                f"Imagine the alternate life where they followed through. "
                f"Second person. Return ONLY prose. 6-8 sentences."
            ),
        },
    }


@router.get("")
async def get_verses(
    user_id: Optional[str] = Query(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Return verses for the 3D map.

    - GET /api/verses?user_id=xxx → public, no auth required
    - GET /api/verses → requires auth, returns your own verses
    """
    if user_id:
        # Public view of someone's map
        target_user_id = user_id
    else:
        # Private view — must be authenticated
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        uid = decode_access_token(credentials.credentials)
        if not uid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        target_user_id = user.id

    result = await db.execute(
        select(PathNotTaken)
        .where(PathNotTaken.user_id == target_user_id)
        .order_by(PathNotTaken.confidence.desc())
    )
    paths = result.scalars().all()
    verses = [path_to_verse(p, i) for i, p in enumerate(paths)]
    return {"verses": verses, "count": len(verses)}


# ─── Claude proxy for narrative generation ───


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 1000


@router.post("/generate")
async def generate_narrative(
    req: GenerateRequest,
    user: User = Depends(get_current_user),
):
    """Proxy to Anthropic API so the frontend doesn't need the API key."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": req.max_tokens,
                "messages": [{"role": "user", "content": req.prompt}],
            },
            timeout=30.0,
        )
        return resp.json()
