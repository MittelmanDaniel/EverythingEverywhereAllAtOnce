import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PathNotTaken(Base):
    __tablename__ = "paths_not_taken"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String)  # abandoned_project, forgotten_interest, dormant_period
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    source_service: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    timeline_date: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
