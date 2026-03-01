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
                if data.service == "github":
                    paths.extend(analyze_github(user_id, parsed))
                elif data.service == "youtube":
                    paths.extend(analyze_youtube(user_id, parsed))
                elif data.service == "goodreads":
                    paths.extend(analyze_goodreads(user_id, parsed))
            except Exception as e:
                logger.error(f"Analysis failed for {data.service}: {e}")

        for p in paths:
            db.add(p)
        await db.commit()


def analyze_github(user_id: str, data: dict) -> list[PathNotTaken]:
    paths = []
    repos = data.get("repos", [])

    for repo in repos:
        if repo.get("is_fork"):
            continue
        if not repo.get("has_recent_activity", True):
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="abandoned_project",
                    title=f"The {repo['name']} Project",
                    description=(
                        f"You created '{repo['name']}'"
                        f"{' (' + repo['language'] + ')' if repo.get('language') else ''}"
                        f" and last touched it {repo.get('last_commit_date', 'a while ago')}. "
                        f"What were you building? What made you stop?"
                    ),
                    evidence_json=json.dumps({"repo": repo}),
                    source_service="github",
                    confidence=0.8,
                    timeline_date=repo.get("last_commit_date"),
                )
            )

    # Interest clusters from stars
    starred = data.get("starred_repos", [])
    topic_counts: dict[str, list] = {}
    for s in starred:
        for tag in s.get("topic_tags", []):
            topic_counts.setdefault(tag, []).append(s)

    repo_languages = {r.get("language", "").lower() for r in repos if r.get("language")}

    for topic, starred_repos in topic_counts.items():
        if topic.lower() not in repo_languages and len(starred_repos) >= 3:
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="forgotten_interest",
                    title=f"Your {topic.title()} Curiosity",
                    description=(
                        f"You starred {len(starred_repos)} repos about {topic} "
                        f"but never built a {topic} project yourself. "
                        f"Was this a road you considered taking?"
                    ),
                    evidence_json=json.dumps({"starred": starred_repos[:5]}),
                    source_service="github",
                    confidence=0.6,
                )
            )

    # Contribution gaps
    years = data.get("contribution_years", [])
    if len(years) >= 2:
        all_years = range(min(years), max(years) + 1)
        gaps = [y for y in all_years if y not in years]
        if gaps:
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="dormant_period",
                    title=f"The Quiet Year{'s' if len(gaps) > 1 else ''}: {', '.join(map(str, gaps))}",
                    description=(
                        f"Your GitHub went silent in {', '.join(map(str, gaps))}. "
                        f"What were you doing instead? Sometimes the paths we take offline "
                        f"matter more than the code we write."
                    ),
                    evidence_json=json.dumps({"gap_years": gaps}),
                    source_service="github",
                    confidence=0.5,
                    timeline_date=str(gaps[0]),
                )
            )

    return paths


def analyze_youtube(user_id: str, data: dict) -> list[PathNotTaken]:
    paths = []

    for playlist in data.get("playlists", []):
        if playlist.get("is_watch_later"):
            if playlist.get("video_count", 0) > 10:
                paths.append(
                    PathNotTaken(
                        user_id=user_id,
                        category="forgotten_interest",
                        title="The Watch Later Graveyard",
                        description=(
                            f"You have {playlist['video_count']} videos saved for 'later'. "
                            f"Each one was something that caught your attention, "
                            f"a spark of curiosity you planned to follow up on."
                        ),
                        evidence_json=json.dumps({"playlist": playlist}),
                        source_service="youtube",
                        confidence=0.7,
                    )
                )
        elif playlist.get("video_count", 0) > 5:
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="forgotten_interest",
                    title=f"Your '{playlist['title']}' Collection",
                    description=(
                        f"You curated {playlist['video_count']} videos in '{playlist['title']}'. "
                        f"Last updated {playlist.get('last_updated', 'unknown')}. "
                        f"This was something you cared about enough to organize."
                    ),
                    evidence_json=json.dumps({"playlist": playlist}),
                    source_service="youtube",
                    confidence=0.7,
                    timeline_date=playlist.get("last_updated"),
                )
            )

    return paths


def analyze_goodreads(user_id: str, data: dict) -> list[PathNotTaken]:
    paths = []

    for book in data.get("books", []):
        if book.get("shelf") == "currently-reading":
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="abandoned_project",
                    title=f"Unfinished: '{book['title']}'",
                    description=(
                        f"You started reading '{book['title']}' by {book.get('author', 'unknown')} "
                        f"but it's still marked as 'currently reading'. "
                        f"Some books change us even unfinished — what did this one teach you?"
                    ),
                    evidence_json=json.dumps({"book": book}),
                    source_service="goodreads",
                    confidence=0.8,
                    timeline_date=book.get("date_added"),
                )
            )
        elif book.get("shelf") == "to-read":
            paths.append(
                PathNotTaken(
                    user_id=user_id,
                    category="forgotten_interest",
                    title=f"'{book['title']}' by {book.get('author', 'unknown')}",
                    description=(
                        f"You added this to your reading list"
                        f"{' on ' + book['date_added'] if book.get('date_added') else ''}. "
                        f"What drew you to it? The person who saved this book "
                        f"was curious about something."
                    ),
                    evidence_json=json.dumps({"book": book}),
                    source_service="goodreads",
                    confidence=0.5,
                    timeline_date=book.get("date_added"),
                )
            )

    # Reading challenge
    goal = data.get("reading_challenge_goal")
    progress = data.get("reading_challenge_progress", 0)
    if goal and progress < goal:
        paths.append(
            PathNotTaken(
                user_id=user_id,
                category="abandoned_project",
                title=f"Reading Challenge: {progress}/{goal} Books",
                description=(
                    f"You set out to read {goal} books but made it to {progress}. "
                    f"The ambition to read more was real — what got in the way?"
                ),
                evidence_json=json.dumps({"goal": goal, "progress": progress}),
                source_service="goodreads",
                confidence=0.6,
            )
        )

    return paths
