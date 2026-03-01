from pydantic import BaseModel


class HistoryEntry(BaseModel):
    title: str
    url: str | None = None
    timestamp: str | None = None
    source: str | None = None  # "Google Search", "Chrome", "YouTube", etc.


class BrowserHistoryData(BaseModel):
    entries: list[HistoryEntry] = []
