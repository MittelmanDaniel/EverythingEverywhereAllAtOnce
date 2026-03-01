from pydantic import BaseModel


class GitHubRepo(BaseModel):
    name: str
    description: str | None = None
    language: str | None = None
    stars: int = 0
    last_commit_date: str | None = None
    is_fork: bool = False
    has_recent_activity: bool = True


class GitHubStarredRepo(BaseModel):
    name: str
    owner: str
    description: str | None = None
    topic_tags: list[str] = []


class GitHubData(BaseModel):
    username: str
    repos: list[GitHubRepo] = []
    starred_repos: list[GitHubStarredRepo] = []
    contribution_years: list[int] = []
    bio: str | None = None
