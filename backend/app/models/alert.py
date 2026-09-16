from sqlalchemy import Boolean, BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    comment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE")
    )
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    comment = relationship("Comment", back_populates="alerts")
