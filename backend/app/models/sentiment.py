from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    sentiment: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    severity: Mapped[int | None] = mapped_column(SmallInteger)
    topic: Mapped[str | None] = mapped_column(String(50))
    analyzed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    comment = relationship("Comment", back_populates="sentiment_analysis")
