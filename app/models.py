from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog import MEASUREMENT_KEYS
from app.db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Commission(Base):
    """A request from the commission form: a Register signup, a time-of-need request, or a consultation."""

    __tablename__ = "commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    plan: Mapped[str] = mapped_column(String(20))  # recent | register | ahead
    status: Mapped[str] = mapped_column(String(20), default="new")

    dog_name: Mapped[str] = mapped_column(String(120))
    breed: Mapped[str] = mapped_column(String(120), default="")
    tier: Mapped[str] = mapped_column(String(20))
    pose: Mapped[str] = mapped_column(String(60), default="")
    story: Mapped[str] = mapped_column(Text, default="")

    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(40))
    city: Mapped[str] = mapped_column(String(120), default="")
    contact: Mapped[str] = mapped_column(String(40), default="")
    vet: Mapped[str] = mapped_column(String(240), default="")

    # Private link to the likeness page. Register only.
    token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)

    media: Mapped[list["Media"]] = relationship(back_populates="commission", cascade="all, delete-orphan", order_by="Media.id")
    measurements: Mapped[list["MeasurementSet"]] = relationship(back_populates="commission", cascade="all, delete-orphan", order_by="MeasurementSet.id")


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commission_id: Mapped[int] = mapped_column(ForeignKey("commissions.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    slot: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(10))  # photo | video
    original_name: Mapped[str] = mapped_column(String(255), default="")
    stored_name: Mapped[str] = mapped_column(String(80), unique=True)
    content_type: Mapped[str] = mapped_column(String(60))
    size_bytes: Mapped[int] = mapped_column(Integer)

    commission: Mapped[Commission] = relationship(back_populates="media")


class MeasurementSet(Base):
    """One round of measurements, taken on one day. We average across rounds."""

    __tablename__ = "measurement_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commission_id: Mapped[int] = mapped_column(ForeignKey("commissions.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    taken_on: Mapped[date] = mapped_column(Date)
    unit: Mapped[str] = mapped_column(String(2))  # in | cm
    notes: Mapped[str] = mapped_column(Text, default="")

    nose_to_tail: Mapped[float | None] = mapped_column(Float, nullable=True)
    withers_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    chest_girth: Mapped[float | None] = mapped_column(Float, nullable=True)
    neck: Mapped[float | None] = mapped_column(Float, nullable=True)
    head_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    head_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    front_paw_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    front_paw_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    rear_paw_width: Mapped[float | None] = mapped_column(Float, nullable=True)
    rear_paw_length: Mapped[float | None] = mapped_column(Float, nullable=True)

    commission: Mapped[Commission] = relationship(back_populates="measurements")

    def values(self) -> dict[str, float | None]:
        return {k: getattr(self, k) for k in MEASUREMENT_KEYS}
