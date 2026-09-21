import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ClinicService(Base):
    __tablename__ = "clinic_services"
    __table_args__ = (CheckConstraint("price >= 0 AND minutes > 0 AND version > 0"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    minutes: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
