from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import db

if TYPE_CHECKING:
    from models.user import User


INCOME_SOURCES = (
    "Salary",
    "Freelance",
    "Business",
    "Investments",
    "Rental",
    "Gift",
    "Refund",
    "Other",
)


class Income(db.Model):
    """A single income entry owned by one user."""

    __tablename__ = "incomes"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_incomes_positive_amount"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(db.Numeric(12, 2), nullable=False)
    source: Mapped[str] = mapped_column(db.String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(db.String(255))
    income_date: Mapped[date] = mapped_column(
        db.Date, nullable=False, default=date.today, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="incomes")

    def __repr__(self) -> str:
        return f"<Income {self.source}: {self.amount}>"
