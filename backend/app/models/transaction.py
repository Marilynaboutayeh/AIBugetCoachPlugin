from datetime import datetime
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)

    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(10), nullable=True)

    merchant_description: Mapped[str] = mapped_column(String, nullable=False)
    mcc: Mapped[str] = mapped_column(String(10), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)

    predicted_main_category: Mapped[str | None] = mapped_column(String, nullable=True)
    predicted_main_category_description: Mapped[str | None] = mapped_column(String, nullable=True)

    predicted_subcategory: Mapped[str | None] = mapped_column(String, nullable=True)
    predicted_subcategory_description: Mapped[str | None] = mapped_column(String, nullable=True)

    predicted_sub_subcategory: Mapped[str | None] = mapped_column(String, nullable=True)

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matched_by: Mapped[str | None] = mapped_column(String(50), nullable=True)