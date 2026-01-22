"""Base model with common fields."""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
