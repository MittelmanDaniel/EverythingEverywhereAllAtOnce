from pydantic import BaseModel


class GoodreadsBook(BaseModel):
    title: str
    author: str
    shelf: str  # "to-read", "currently-reading", "read"
    date_added: str | None = None
    rating: int | None = None
    pages: int | None = None


class GoodreadsData(BaseModel):
    books: list[GoodreadsBook] = []
    total_books_read: int = 0
    reading_challenge_goal: int | None = None
    reading_challenge_progress: int | None = None
