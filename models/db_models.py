import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class AuditRecord(Base):
    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    resume_text: Mapped[str] = mapped_column(String)
    jd_text: Mapped[str] = mapped_column(String)
    fit_score: Mapped[int] = mapped_column(Integer)
    total_requirements: Mapped[int] = mapped_column(Integer)
    risk_flags: Mapped[int] = mapped_column(Integer)
    verified: Mapped[int] = mapped_column(Integer)
    verdicts: Mapped[list] = mapped_column(JSON)