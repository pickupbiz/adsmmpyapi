"""Part models for aerospace components."""
import enum
from typing import Optional, List
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin


class PartStatus(str, enum.Enum):
    """Part status enumeration."""
    DESIGN = "design"
    PROTOTYPE = "prototype"
    PRODUCTION = "production"
    OBSOLETE = "obsolete"
    RESTRICTED = "restricted"


class PartCriticality(str, enum.Enum):
    """Part criticality level for aerospace applications."""
    CRITICAL = "critical"  # Flight-critical components
    MAJOR = "major"  # Major structural components
    MINOR = "minor"  # Minor components
    STANDARD = "standard"  # Standard parts


class Part(Base, TimestampMixin):
    """Aerospace part model."""
    
    __tablename__ = "parts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    part_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    revision: Mapped[str] = mapped_column(String(10), default="A", nullable=False)
    
    # Classification
    status: Mapped[PartStatus] = mapped_column(
        Enum(PartStatus),
        default=PartStatus.DESIGN,
        nullable=False
    )
    criticality: Mapped[PartCriticality] = mapped_column(
        Enum(PartCriticality),
        default=PartCriticality.STANDARD,
        nullable=False
    )
    
    # Specifications
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    drawing_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    weight_unit: Mapped[str] = mapped_column(String(10), default="kg", nullable=False)
    
    # Assembly hierarchy
    parent_part_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("parts.id"),
        nullable=True
    )
    
    # Compliance
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_inspection: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inspection_interval_hours: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Cost
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(14, 4), nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Relationships
    parent_part = relationship("Part", remote_side="Part.id", backref="child_parts")
    part_materials = relationship("PartMaterial", back_populates="part")
    
    def __repr__(self) -> str:
        return f"<Part(id={self.id}, part_number='{self.part_number}', name='{self.name}')>"


class PartMaterial(Base, TimestampMixin):
    """Association table linking parts to their required materials."""
    
    __tablename__ = "part_materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    quantity_required: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    part = relationship("Part", back_populates="part_materials")
    material = relationship("Material", back_populates="part_materials")
    
    def __repr__(self) -> str:
        return f"<PartMaterial(part_id={self.part_id}, material_id={self.material_id})>"
