"""Inventory models for material tracking."""
import enum
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin


class InventoryStatus(str, enum.Enum):
    """Inventory status enumeration."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"
    CONSUMED = "consumed"


class TransactionType(str, enum.Enum):
    """Inventory transaction type enumeration."""
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    SCRAP = "scrap"
    QUARANTINE = "quarantine"
    RELEASE = "release"


class Inventory(Base, TimestampMixin):
    """Inventory model for tracking material stock."""
    
    __tablename__ = "inventory"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    # Lot and batch tracking
    lot_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantity
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Status and location
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        default=InventoryStatus.AVAILABLE,
        nullable=False
    )
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    bin_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Dates
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    manufacture_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Traceability
    certificate_of_conformance: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    heat_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mill_test_report: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Cost
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    material = relationship("Material", back_populates="inventory")
    transactions = relationship("InventoryTransaction", back_populates="inventory")
    
    @property
    def available_quantity(self) -> float:
        """Calculate available quantity (total - reserved)."""
        return float(self.quantity) - float(self.reserved_quantity)
    
    @property
    def is_expired(self) -> bool:
        """Check if inventory item is expired."""
        if self.expiration_date:
            return date.today() > self.expiration_date
        return False
    
    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, lot='{self.lot_number}', qty={self.quantity})>"


class InventoryTransaction(Base, TimestampMixin):
    """Transaction log for inventory movements."""
    
    __tablename__ = "inventory_transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), nullable=False)
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType),
        nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Reference
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Location tracking for transfers
    from_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    to_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="transactions")
    performed_by_user = relationship("User", back_populates="inventory_transactions")
    
    def __repr__(self) -> str:
        return f"<InventoryTransaction(id={self.id}, type='{self.transaction_type}', qty={self.quantity})>"
