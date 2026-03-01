import hashlib
import json
import logging

from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import create_session, get_client
from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.analysis import PathNotTaken
from app.models.user import User
from app.utils.security import decode_access_token

logger = logging.getLogger(__name__)

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

    video = evidence.get("video", "") if isinstance(evidence, dict) else ""

    zone_label = ZONES[zone]

    return {
        "id": path.id,
        "y": year,
        "mo": month,
        "url": url,
        "video": video,
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


# ─── Explore a verse: live Browser Use session ───


class ExploreRequest(BaseModel):
    verse_id: str = ""
    title: str
    description: str
    url: str = ""
    evidence_json: str = "{}"


async def _run_explore_agent(session_id: str, task: str):
    """Background task: run the explore agent in the user's live session."""
    client = get_client()
    try:
        result = client.run(task=task, session_id=session_id)
        await result
        logger.info(f"Explore agent completed for session {session_id}")
    except Exception as e:
        logger.error(f"Explore agent failed for session {session_id}: {e}")
    finally:
        await client.close()


@router.post("/explore")
async def explore_verse(
    req: ExploreRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Create a live browser session and start an agent to explore a verse."""
    is_yc_demo = (
        req.verse_id == "demo-verse-006-yc-app"
        or "yc w23 application" in req.title.lower()
    )

    # Figure out a starting URL from the evidence
    evidence = {}
    try:
        evidence = json.loads(req.evidence_json) if req.evidence_json else {}
    except json.JSONDecodeError:
        pass

    # Use the provided URL only if it starts with http(s)
    start_url = req.url if req.url.startswith("http") else ""
    if not start_url:
        raw = evidence.get("url", "")
        if raw.startswith("http"):
            start_url = raw
    # Fall back to a Google search for the title
    if not start_url:
        start_url = f"https://www.google.com/search?q={req.title.replace(' ', '+')}"
    # YC demo: begin with idea research first, not on the YC page.
    if is_yc_demo:
        start_url = "https://www.google.com/search?q=palantir+for+hollywood+startup+ideas"

    session_id, live_url = await create_session(start_url=start_url)

    if is_yc_demo:
        task = f"""You are helping a user finally follow through on something they hesitated to do.

Background: {req.title}
{req.description}

Follow this exact sequence:

STEP 1 — RESEARCH (spend real time here, do not rush):
You are on a Google search results page for "palantir for hollywood startup ideas".
- Click on at least 3 different search results that look relevant to data analytics, AI, or tech for the entertainment/Hollywood industry.
- For each result, actually READ the page content — scroll down, look for key insights, market data, competitor info, or interesting angles.
- After reading each page, use the browser back button or open a new search to continue exploring.
- Try at least one more search query like "AI tools for film production" or "entertainment industry data analytics startups" and click through those results too.
- You should spend meaningful time on this step — click links, scroll pages, read articles. Do NOT just glance at the Google results page and move on.

STEP 2 — NAVIGATE TO YC:
Once you have gathered insights from multiple sources, navigate to: https://www.ycombinator.com/apply

STEP 3 — WAIT:
Stop there and wait for user input before filling or submitting any form fields.

Your job is to help the user actually DO the thing they never did — sign up, book it, apply, finish it, send it, buy it, whatever it was.
Be proactive and action-oriented. Don't just show them information — help them take the first real step.
The user can see and interact with the browser alongside you.
Do not fill any application form fields until the user explicitly asks you to continue.
"""
    else:
        is_google_search = start_url.startswith("https://www.google.com/search")
        if is_google_search:
            research_instructions = f"""You are on a Google search results page. Do NOT just look at it and stop.
- Click on at least 2-3 search results that look most relevant to "{req.title}".
- For each result, actually READ the page — scroll down, look for useful information, actionable links, sign-up pages, or next steps.
- After reading each page, navigate back or search again to explore more angles.
- Once you have enough context, find the most actionable next step (a sign-up page, application form, booking site, etc.) and navigate there."""
        else:
            research_instructions = f"""Navigate to {start_url}.
- Actually explore the page — scroll down, read the content, click on relevant links.
- Look for actionable next steps: sign-up buttons, application forms, booking options, purchase links, etc.
- If this is a search page, click on at least 2-3 results and read them before deciding on a next step."""

        task = f"""You are helping a user finally follow through on something they hesitated to do.

Background: {req.title}
{req.description}

{research_instructions}

Your job is to help the user actually DO the thing they never did — sign up, book it, apply, finish it, send it, buy it, whatever it was.
Be proactive and action-oriented. Don't just show them information — help them take the first real step.
The user can see and interact with the browser alongside you.
If you need the user to log in or take action, pause and wait for them.
"""

    background_tasks.add_task(_run_explore_agent, session_id, task)
    return {"session_id": session_id, "live_url": live_url}
