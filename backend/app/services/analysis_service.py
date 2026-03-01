import json
import logging

from sqlalchemy import delete, select

from app.database import async_session
from app.models.analysis import PathNotTaken
from app.models.collected_data import CollectedData

logger = logging.getLogger(__name__)


async def run_analysis(user_id: str):
    """Analyze collected data and generate 'paths not taken'."""
    async with async_session() as db:
        # Get all collected data
        result = await db.execute(
            select(CollectedData).where(CollectedData.user_id == user_id)
        )
        all_data = result.scalars().all()

        if not all_data:
            return

        # Clear previous analysis
        await db.execute(delete(PathNotTaken).where(PathNotTaken.user_id == user_id))

        paths: list[PathNotTaken] = []

        for data in all_data:
            try:
                parsed = json.loads(data.data_json)
                if data.service == "google" and data.data_type == "history":
                    paths.extend(analyze_browser_history(user_id, parsed))
                elif data.service == "google":
                    paths.extend(analyze_google(user_id, parsed))
            except Exception as e:
                logger.error(f"Analysis failed for {data.service}: {e}")

        for p in paths:
            db.add(p)
        await db.commit()


def analyze_google(user_id: str, data: dict) -> list[PathNotTaken]:
    paths = []

    # Abandoned docs: created but barely edited or untouched for months
    for doc in data.get("docs", []):
        last_edited = doc.get("last_edited")
        created = doc.get("created_date")
        word_count = doc.get("word_count")

        # Docs with very little content suggest abandoned ideas
        if word_count is not None and word_count < 50:
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="abandoned_project",
                    title=f"The Empty Doc: '{doc['title']}'",
                    description=(
                        f"You created '{doc['title']}' "
                        f"{'on ' + created if created else 'some time ago'} "
                        f"but it only has {word_count} words. "
                        f"What were you about to write? What idea were you chasing?"
                    ),
                    evidence_json=json.dumps({"doc": doc}),
                    source_service="google",
                    confidence=0.8,
                    timeline_date=created or last_edited,
                )
            )

    # Unsent drafts: Gmail drafts that were never sent
    for draft in data.get("drafts", []):
        subject = draft.get("subject") or "(no subject)"
        paths.append(
            PathNotTaken(
                user_id=user_id,
                category="forgotten_interest",
                title=f"Unsent: '{subject}'",
                description=(
                    f"You composed a draft"
                    f"{' about \"' + subject + '\"' if draft.get('subject') else ''}"
                    f"{' on ' + draft['created_date'] if draft.get('created_date') else ''}"
                    f" but never hit send. "
                    f"What stopped you? Sometimes the things we almost say matter most."
                ),
                evidence_json=json.dumps({"draft": draft}),
                source_service="google",
                confidence=0.7,
                timeline_date=draft.get("created_date"),
            )
        )

    # Forgotten files: Drive files not opened in a long time
    for f in data.get("drive_files", []):
        last_opened = f.get("last_opened_by_me")
        created = f.get("created_date")

        # Files that were created but seemingly never revisited
        if created and not last_opened:
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="forgotten_interest",
                    title=f"Forgotten: '{f['name']}'",
                    description=(
                        f"You created '{f['name']}'"
                        + (f" ({f['type']})" if f.get("type") else "")
                        + f" on {created} but never opened it again. "
                        f"What was this for? A project that never took off?"
                    ),
                    evidence_json=json.dumps({"file": f}),
                    source_service="google",
                    confidence=0.6,
                    timeline_date=created,
                )
            )

    # Quiet periods: look for gaps in file creation activity
    all_dates = []
    for f in data.get("drive_files", []):
        if f.get("created_date"):
            try:
                year = int(f["created_date"][:4])
                all_dates.append(year)
            except (ValueError, IndexError):
                pass
    for doc in data.get("docs", []):
        if doc.get("created_date"):
            try:
                year = int(doc["created_date"][:4])
                all_dates.append(year)
            except (ValueError, IndexError):
                pass

    if len(set(all_dates)) >= 2:
        years = sorted(set(all_dates))
        all_years = range(min(years), max(years) + 1)
        gaps = [y for y in all_years if y not in years]
        if gaps:
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="dormant_period",
                    title=f"The Quiet Year{'s' if len(gaps) > 1 else ''}: {', '.join(map(str, gaps))}",
                    description=(
                        f"Your Google Drive went silent in {', '.join(map(str, gaps))}. "
                        f"No new files or docs created. What were you doing instead? "
                        f"Sometimes the paths we take offline matter more."
                    ),
                    evidence_json=json.dumps({"gap_years": gaps}),
                    source_service="google",
                    confidence=0.5,
                    timeline_date=str(gaps[0]),
                )
            )

    return paths


def analyze_browser_history(user_id: str, entries: list[dict]) -> list[PathNotTaken]:
    from collections import Counter
    from urllib.parse import urlparse

    paths = []

    # Group visits by domain
    domain_visits: dict[str, list[dict]] = {}
    for entry in entries:
        try:
            domain = urlparse(entry["url"]).netloc
        except Exception:
            continue
        domain_visits.setdefault(domain, []).append(entry)

    # Find abandoned sites: domains visited many times but not recently
    # Sort entries by last_visit_time to find what's recent vs old
    all_times = []
    for entry in entries:
        t = entry.get("last_visit_time")
        if t:
            all_times.append(t)
    all_times.sort()

    if len(all_times) >= 2:
        # Use the median as a rough "recent" cutoff
        midpoint = all_times[len(all_times) // 2]

        for domain, visits in domain_visits.items():
            # Skip common/utility sites
            if any(skip in domain for skip in [
                "google", "facebook", "twitter", "x.com",
                "localhost", "127.0.0.1", "chrome", "new-tab",
            ]):
                continue

            total_visits = sum(v.get("visit_count", 1) for v in visits)
            if total_visits < 5:
                continue

            # Check if all visits are old (before midpoint)
            recent = [v for v in visits if (v.get("last_visit_time") or "") >= midpoint]
            if len(recent) == 0:
                # All visits are old — this is an abandoned site
                top_title = max(visits, key=lambda v: v.get("visit_count", 0)).get("title", domain)
                paths.append(
                    PathNotTaken(
                        user_id=user_id,
                        category="forgotten_interest",
                        title=f"You Used to Visit: {domain}",
                        description=(
                            f"You visited {domain} at least {total_visits} times "
                            f"(e.g. \"{top_title}\") but haven't been back recently. "
                            f"What drew you there? What changed?"
                        ),
                        evidence_json=json.dumps({
                            "domain": domain,
                            "total_visits": total_visits,
                            "sample_pages": [v.get("title") for v in visits[:5]],
                        }),
                        source_service="google",
                        confidence=0.6,
                        timeline_date=visits[0].get("last_visit_time", "")[:10],
                    )
                )

    # Find rabbit holes: single-session deep dives (many pages on one domain)
    domain_page_counts = {d: len(v) for d, v in domain_visits.items()}
    for domain, count in sorted(domain_page_counts.items(), key=lambda x: -x[1]):
        if count < 15:
            break
        if any(skip in domain for skip in [
            "google", "facebook", "twitter", "x.com",
            "youtube", "reddit", "github",
            "localhost", "127.0.0.1", "chrome",
        ]):
            continue

        sample_titles = [v.get("title", "") for v in domain_visits[domain][:5]]
        paths.append(
            PathNotTaken(
                user_id=user_id,
                category="forgotten_interest",
                title=f"Deep Dive: {domain}",
                description=(
                    f"You visited {count} different pages on {domain}. "
                    f"That's a serious rabbit hole. What were you researching?"
                ),
                evidence_json=json.dumps({
                    "domain": domain,
                    "page_count": count,
                    "sample_titles": sample_titles,
                }),
                source_service="google",
                confidence=0.5,
            )
        )

        if len([p for p in paths if "Deep Dive" in p.title]) >= 5:
            break

    return paths
