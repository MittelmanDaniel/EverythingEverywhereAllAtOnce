from pydantic import BaseModel


class CookieItem(BaseModel):
    name: str
    value: str
    domain: str
    path: str = "/"
    secure: bool = False
    httpOnly: bool = False
    sameSite: str | None = None
    expirationDate: float | None = None


class CookieSubmission(BaseModel):
    service: str  # "github", "youtube", "goodreads"
    cookies: list[CookieItem]


class BulkCookieSubmission(BaseModel):
    cookies: list[CookieItem]


class HistoryEntry(BaseModel):
    url: str
    title: str
    visit_count: int = 0
    last_visit_time: str | None = None


class HistorySubmission(BaseModel):
    entries: list[HistoryEntry]
