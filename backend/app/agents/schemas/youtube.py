from pydantic import BaseModel


class YouTubePlaylist(BaseModel):
    title: str
    video_count: int = 0
    last_updated: str | None = None
    is_watch_later: bool = False


class YouTubeSubscription(BaseModel):
    channel_name: str
    category: str | None = None
    last_upload: str | None = None


class YouTubeData(BaseModel):
    playlists: list[YouTubePlaylist] = []
    subscriptions: list[YouTubeSubscription] = []
