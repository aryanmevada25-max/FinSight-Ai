from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import bcrypt, db, login_manager


class User(db.Model, UserMixin):
    """Application user and authentication credentials."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        db.String(120), unique=True, nullable=False, index=True
    )
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    currency: Mapped[str] = mapped_column(
        db.String(3), nullable=False, default="USD", server_default="USD"
    )
    monthly_budget: Mapped[Decimal] = mapped_column(
        db.Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    incomes: Mapped[list["Income"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, plain_text_password: str) -> None:
        """Hash and store a password."""
        self.password = bcrypt.generate_password_hash(
            plain_text_password
        ).decode("utf-8")

    def check_password(self, plain_text_password: str) -> bool:
        """Check a password against the stored hash."""
        return bcrypt.check_password_hash(self.password, plain_text_password)

    def __repr__(self) -> str:
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
