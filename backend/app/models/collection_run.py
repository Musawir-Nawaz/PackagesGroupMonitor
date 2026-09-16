from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    items_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_duplicate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    error_message: Mapped[str | None] = mapped_column(Text)
