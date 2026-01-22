"""Supplier models for material sourcing."""
import enum
from typing import Optional, List
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin


class SupplierStatus(str, enum.Enum):
    """Supplier status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_APPROVAL = "pending_approval"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class SupplierTier(str, enum.Enum):
    """Supplier tier classification."""
    TIER_1 = "tier_1"  # Primary/direct suppliers
    TIER_2 = "tier_2"  # Secondary suppliers
    TIER_3 = "tier_3"  # Tertiary/backup suppliers


class Supplier(Base, TimestampMixin):
    """Supplier model for material sourcing."""
    
    __tablename__ = "suppliers"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Status and classification
    status: Mapped[SupplierStatus] = mapped_column(
        Enum(SupplierStatus),
        default=SupplierStatus.PENDING_APPROVAL,
        nullable=False
    )
    tier: Mapped[SupplierTier] = mapped_column(
        Enum(SupplierTier),
        default=SupplierTier.TIER_2,
        nullable=False
    )
    
    # Contact information
    contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Address
    address_line_1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="USA", nullable=False)
    
    # Certifications and compliance
    is_as9100_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_nadcap_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_itar_compliant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cage_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Commercial and Govt Entity Code
    
    # Performance metrics
    quality_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    delivery_rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    supplier_materials = relationship("SupplierMaterial", back_populates="supplier")
    orders = relationship("Order", back_populates="supplier")
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, code='{self.code}', name='{self.name}')>"


class SupplierMaterial(Base, TimestampMixin):
    """Association table linking suppliers to materials they provide."""
    
    __tablename__ = "supplier_materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    # Supplier-specific details
    supplier_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    minimum_order_quantity: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_materials")
    material = relationship("Material", back_populates="supplier_materials")
    
    def __repr__(self) -> str:
        return f"<SupplierMaterial(supplier_id={self.supplier_id}, material_id={self.material_id})>"
