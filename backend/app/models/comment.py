from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    post_id: Mapped[str | None] = mapped_column(String(255))
    comment_id: Mapped[str | None] = mapped_column(String(255))
    post_url: Mapped[str | None] = mapped_column(Text)
    comment_url: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    engagement: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    collected_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_relevant: Mapped[bool | None] = mapped_column(Boolean)
    dedup_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    sentiment_analysis = relationship(
        "SentimentAnalysis", back_populates="comment", uselist=False, cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="comment", cascade="all, delete-orphan")
