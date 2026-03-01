"""Seed demo user with hardcoded verses from the original map.html.

Run:  cd backend && python seed_demo.py
Idempotent — deletes old demo paths, re-inserts.
"""

import asyncio
import json

from sqlalchemy import delete

from app.config import settings  # noqa: F401  (ensures env loads)
from app.database import Base, engine, async_session, init_db
from app.models.user import User
from app.models.analysis import PathNotTaken
from app.utils.security import hash_password

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_EMAIL = "aditri@everythingeverywhere.app"
DEMO_PASSWORD = "demo1234"

# The 12 original verses from map.html, mapped to PathNotTaken fields.
# Each has a deterministic ID so colors (derived from _stable_hash(id)) are stable across re-seeds.
DEMO_PATHS = [
    {
        "id": "demo-verse-001-half-moon-bay",
        "category": "forgotten_interest",
        "title": "Directions to Half Moon Bay — checked 14 times",
        "description": "You never went. You kept measuring the distance.",
        "source_service": "google",
        "confidence": 0.85,
        "timeline_date": "2022-02",
        "evidence_json": json.dumps({"url": "https://www.google.com/maps/dir/San+Francisco/Half+Moon+Bay"}),
    },
    {
        "id": "demo-verse-002-untitled-doc",
        "category": "abandoned_project",
        "title": "Untitled Google Doc — 4,200 words, never shared",
        "description": "It started 'Dear —' and you never filled in the name.",
        "source_service": "google",
        "confidence": 0.9,
        "timeline_date": "2019-12",
        "evidence_json": json.dumps({"url": "https://docs.google.com/document/create"}),
    },
    {
        "id": "demo-verse-003-swan-lake",
        "category": "dormant_period",
        "title": "Two tickets to Swan Lake, never purchased",
        "description": "You typed their name into the guest field and closed the tab.",
        "source_service": "google",
        "confidence": 0.7,
        "timeline_date": "2018-03",
        "evidence_json": json.dumps({"url": "https://www.sfballet.org/2025-2026-season/", "video": "/videos/swan-lake.mp4"}),
    },
    {
        "id": "demo-verse-004-career-change",
        "category": "abandoned_project",
        "title": '"Is it too late to change careers at 27"',
        "description": "Searched at 2:47am. Also: 'careers that feel like play.'",
        "source_service": "google",
        "confidence": 0.65,
        "timeline_date": "2020-11",
        "evidence_json": json.dumps({"url": "https://www.google.com/search?q=is+it+too+late+to+change+careers+at+27"}),
    },
    {
        "id": "demo-verse-005-manuscript",
        "category": "abandoned_project",
        "title": "The manuscript — 41,000 words, abandoned at the climax",
        "description": "You stopped writing when the protagonist had to make the choice you couldn't.",
        "source_service": "google",
        "confidence": 0.8,
        "timeline_date": "2021-01",
        "evidence_json": json.dumps({"url": "https://docs.google.com/document/create", "video": "/videos/manuscript.mp4"}),
    },
    {
        "id": "demo-verse-006-yc-app",
        "category": "abandoned_project",
        "title": "YC W23 application — completed, never submitted",
        "description": "You rewatched the demo video 11 times and closed the tab at 11:58pm.",
        "source_service": "google",
        "confidence": 0.75,
        "timeline_date": "2022-10",
        "evidence_json": json.dumps({"url": "https://www.ycombinator.com/apply", "video": "/videos/yc-app.mp4"}),
    },
    {
        "id": "demo-verse-007-alfama-studio",
        "category": "forgotten_interest",
        "title": "Artist studio in Alfama — saved but never booked",
        "description": "You bookmarked it three separate times over two years.",
        "source_service": "google",
        "confidence": 0.55,
        "timeline_date": "2019-08",
        "evidence_json": json.dumps({"url": "https://www.airbnb.com/s/Alfama--Lisbon/homes?query=artist+studio"}),
    },
    {
        "id": "demo-verse-008-silent-retreat",
        "category": "forgotten_interest",
        "title": "10-day silent retreat — application left open 3 weeks",
        "description": "Everything filled except the emergency contact field.",
        "source_service": "google",
        "confidence": 0.5,
        "timeline_date": "2021-05",
        "evidence_json": json.dumps({"url": "https://www.dhamma.org/en/schedules/schmahi"}),
    },
    {
        "id": "demo-verse-009-dream-journal",
        "category": "dormant_period",
        "title": "dream-journal-ai — 3 commits, then silence",
        "description": "Last commit: 'this might actually be something.'",
        "source_service": "google",
        "confidence": 0.45,
        "timeline_date": "2017-10",
        "evidence_json": json.dumps({"url": "https://github.com/new"}),
    },
    {
        "id": "demo-verse-010-disappear-films",
        "category": "dormant_period",
        "title": '"Films about people who disappear" — 23 films',
        "description": "You watched seven in one weekend.",
        "source_service": "google",
        "confidence": 0.4,
        "timeline_date": "2023-07",
        "evidence_json": json.dumps({"url": "https://letterboxd.com/search/films/about+people+who+disappear/"}),
    },
    {
        "id": "demo-verse-011-van-conversion",
        "category": "dormant_period",
        "title": "DIY van conversion guide — 47 tabs open simultaneously",
        "description": "You priced out solar panels at 3am on a Tuesday.",
        "source_service": "google",
        "confidence": 0.3,
        "timeline_date": "2016-06",
        "evidence_json": json.dumps({"url": "https://www.reddit.com/r/vandwellers/"}),
    },
    {
        "id": "demo-verse-012-juilliard",
        "category": "forgotten_interest",
        "title": "Juilliard MFA Acting — application PDF downloaded twice",
        "description": "You never told anyone you downloaded it.",
        "source_service": "google",
        "confidence": 0.25,
        "timeline_date": "2015-09",
        "evidence_json": json.dumps({"url": "https://apply.juilliard.edu/apply/"}),
    },
]


async def seed():
    await init_db()

    async with async_session() as db:
        # Delete old demo paths and user, then recreate from scratch
        await db.execute(
            delete(PathNotTaken).where(PathNotTaken.user_id == DEMO_USER_ID)
        )
        await db.execute(delete(User).where(User.id == DEMO_USER_ID))
        await db.flush()
        print("Deleted existing demo user and paths (if any)")

        # Create fresh demo user
        user = User(
            id=DEMO_USER_ID,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            onboarding_completed=True,
        )
        db.add(user)

        # Insert fresh paths
        for p in DEMO_PATHS:
            db.add(PathNotTaken(user_id=DEMO_USER_ID, **p))

        await db.commit()
        print(f"Seeded demo user ({DEMO_EMAIL}) with {len(DEMO_PATHS)} paths")


if __name__ == "__main__":
    asyncio.run(seed())
