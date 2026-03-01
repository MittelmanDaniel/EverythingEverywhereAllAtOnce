import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CollectedData(Base):
    __tablename__ = "collected_data"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    service: Mapped[str] = mapped_column(String)
    data_type: Mapped[str] = mapped_column(String)  # "repos", "watch_history", etc.
    data_json: Mapped[str] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
