import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ServiceConnection(Base):
    __tablename__ = "service_connections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    service: Mapped[str] = mapped_column(String)  # "github", "youtube", "goodreads"
    cookies_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(String, default="connected")  # connected, collecting, collected, error
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
