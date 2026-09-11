from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    object_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    tracking_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    bounding_box: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    camera = relationship(
        "Camera",
        back_populates="detections"
    )
