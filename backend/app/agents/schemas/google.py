from pydantic import BaseModel


class GoogleDriveFile(BaseModel):
    name: str
    type: str | None = None  # doc, sheet, slide, folder, etc.
    last_modified: str | None = None
    created_date: str | None = None
    owner: str | None = None
    shared: bool = False
    last_opened_by_me: str | None = None


class GoogleDoc(BaseModel):
    title: str
    last_edited: str | None = None
    word_count: int | None = None
    created_date: str | None = None
    shared_with_count: int = 0


class GmailDraft(BaseModel):
    subject: str | None = None
    snippet: str | None = None
    created_date: str | None = None


class GmailLabel(BaseModel):
    name: str
    message_count: int = 0
    unread_count: int = 0


class GoogleData(BaseModel):
    drive_files: list[GoogleDriveFile] = []
    docs: list[GoogleDoc] = []
    drafts: list[GmailDraft] = []
    labels: list[GmailLabel] = []
