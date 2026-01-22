"""Material models for aerospace parts."""
import enum
from typing import Optional, List
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin


class MaterialType(str, enum.Enum):
    """Material type enumeration."""
    METAL = "metal"
    COMPOSITE = "composite"
    POLYMER = "polymer"
    CERAMIC = "ceramic"
    ALLOY = "alloy"
    COATING = "coating"
    ADHESIVE = "adhesive"
    OTHER = "other"


class MaterialStatus(str, enum.Enum):
    """Material status enumeration."""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    PENDING_APPROVAL = "pending_approval"
    RESTRICTED = "restricted"


class MaterialCategory(Base, TimestampMixin):
    """Material category for classification."""
    
    __tablename__ = "material_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("material_categories.id"),
        nullable=True
    )
    
    # Self-referential relationship for hierarchical categories
    parent = relationship("MaterialCategory", remote_side="MaterialCategory.id", backref="subcategories")
    materials = relationship("Material", back_populates="category")
    
    def __repr__(self) -> str:
        return f"<MaterialCategory(id={self.id}, name='{self.name}')>"


class Material(Base, TimestampMixin):
    """Material model for aerospace parts."""
    
    __tablename__ = "materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    part_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    specification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Classification
    material_type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType),
        default=MaterialType.OTHER,
        nullable=False
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("material_categories.id"),
        nullable=True
    )
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus),
        default=MaterialStatus.ACTIVE,
        nullable=False
    )
    
    # Physical properties
    density: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    tensile_strength: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    yield_strength: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    hardness: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    melting_point: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    
    # Compliance and documentation
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mil_spec: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Military specification
    ams_spec: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Aerospace Material Spec
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shelf_life_days: Mapped[Optional[int]] = mapped_column(nullable=True)
    storage_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Cost tracking
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="kg", nullable=False)
    minimum_order_quantity: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Relationships
    category = relationship("MaterialCategory", back_populates="materials")
    part_materials = relationship("PartMaterial", back_populates="material")
    supplier_materials = relationship("SupplierMaterial", back_populates="material")
    inventory = relationship("Inventory", back_populates="material")
    certifications = relationship("MaterialCertification", back_populates="material")
    order_items = relationship("OrderItem", back_populates="material")
    
    def __repr__(self) -> str:
        return f"<Material(id={self.id}, part_number='{self.part_number}', name='{self.name}')>"
