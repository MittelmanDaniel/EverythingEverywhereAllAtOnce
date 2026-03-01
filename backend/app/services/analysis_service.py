import json
import logging

import anthropic
from sqlalchemy import delete, select

from app.config import settings
from app.database import async_session
from app.models.analysis import PathNotTaken
from app.models.collected_data import CollectedData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an analyst for "Everything Everywhere All at Once" — an app that maps the alternate lives a person almost lived based on their digital footprint.

Given a user's Google data (Drive files, Docs, Gmail drafts, labels), identify the most meaningful "paths not taken" — moments where their life could have branched differently.

Look for:
- Abandoned projects: docs or files that started strong but were never finished
- Unsent messages: drafts that reveal something they wanted to say but didn't
- Forgotten interests: files or docs in domains they clearly cared about but drifted away from
- Dormant periods: gaps or silences in their digital activity
- Hidden ambitions: titles or content that hint at a life they were considering

For each path, assign:
- category: one of "abandoned_project", "forgotten_interest", "dormant_period", "unsent_message", "hidden_ambition"
- title: a short, evocative name for this alternate life branch (e.g. "The Novelist You Almost Became")
- description: 2-3 sentences in second person ("You...") that make this path feel real and emotionally resonant
- evidence: the specific data point(s) that reveal this path (file name, draft subject, etc.)
- action_url: a real, working URL the person would visit RIGHT NOW to pull themselves into this timeline. Not the evidence source — the action destination. For example: if they abandoned a novel, link to docs.google.com/document/create. If they almost booked a trip, link to the booking site. If they considered a career change, link to a job board or application page. Always a real URL that loads.
- confidence: 0.0–1.0 how strongly the data suggests this was a real fork in the road
- timeline_date: approximate date (YYYY-MM-DD or YYYY) if determinable, else null

Return a JSON object with a single key "paths" containing an array of path objects. Return 5–15 paths. Only include paths with confidence >= 0.4."""

def _build_user_message(data: dict) -> str:
    return f"""Here is the user's collected Google data:

{json.dumps(data, indent=2)}

Identify the paths not taken. Return only valid JSON."""


async def run_analysis(user_id: str):
    async with async_session() as db:
        result = await db.execute(
            select(CollectedData).where(CollectedData.user_id == user_id)
        )
        all_data = result.scalars().all()

        if not all_data:
            return

        await db.execute(delete(PathNotTaken).where(PathNotTaken.user_id == user_id))

        # Merge all collected data into one dict for Claude
        merged: dict = {}
        for data in all_data:
            try:
                parsed = json.loads(data.data_json)
                merged.update(parsed)
            except Exception as e:
                logger.error(f"Failed to parse collected data for {data.service}: {e}")

        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_user_message(merged)}],
            )

            raw = message.content[0].text
            # Strip markdown code fences if present
            if raw.strip().startswith("```"):
                raw = raw.strip().split("\n", 1)[1].rsplit("```", 1)[0]

            result_json = json.loads(raw)
            paths_data = result_json.get("paths", [])
        except Exception as e:
            logger.error(f"Claude analysis failed for {user_id}: {e}")
            return

        for p in paths_data:
            try:
                evidence = p.get("evidence", {})
                if isinstance(evidence, str):
                    evidence = {"raw": evidence}
                if p.get("action_url"):
                    evidence["url"] = p["action_url"]
                path = PathNotTaken(
                    user_id=user_id,
                    category=p.get("category", "forgotten_interest"),
                    title=p.get("title", ""),
                    description=p.get("description", ""),
                    evidence_json=json.dumps(evidence),
                    source_service="google",
                    confidence=float(p.get("confidence", 0.5)),
                    timeline_date=p.get("timeline_date"),
                )
                db.add(path)
            except Exception as e:
                logger.error(f"Failed to create path: {e}")

        await db.commit()
        logger.info(f"Analysis complete for {user_id}: {len(paths_data)} paths generated")
