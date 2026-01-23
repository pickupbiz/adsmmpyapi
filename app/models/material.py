"""Material models for aerospace parts."""
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder, POLineItem
    from app.models.supplier import Supplier
    from app.models.project import Project
    from app.models.barcode import BarcodeLabel
    from app.models.user import User
    from app.models.user import User


class MaterialType(str, enum.Enum):
    """Material type enumeration."""
    RAW = "raw"
    WIP = "wip"
    FINISHED = "finished"


class MaterialStatus(str, enum.Enum):
    """Material status enumeration."""
    ORDERED = "ordered"  # New status from PO
    RECEIVED = "received"
    IN_INSPECTION = "in_inspection"
    IN_STORAGE = "in_storage"
    ISSUED = "issued"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    REJECTED = "rejected"


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
    """Material model for aerospace parts with PO integration."""
    
    __tablename__ = "materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    specification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    heat_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="units", nullable=False)
    min_stock_level: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    max_stock_level: Mapped[Optional[float]] = mapped_column(Numeric(14, 4), nullable=True)
    
    # PO Reference
    po_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    po_line_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("po_line_items.id"), nullable=True)
    
    # Supplier info (can be from PO or direct)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    supplier_batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Project reference
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    
    # Classification
    material_type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType, values_callable=lambda x: [e.value for e in x]),
        default=MaterialType.RAW,
        nullable=False
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("material_categories.id"),
        nullable=True
    )
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus, values_callable=lambda x: [e.value for e in x]),
        default=MaterialStatus.ORDERED,
        nullable=False
    )
    
    # Status and tracking
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    storage_bin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Dates
    received_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    inspection_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    production_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Quality
    qa_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Pass, Fail, Hold
    qa_inspected_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Barcode
    barcode_id: Mapped[Optional[int]] = mapped_column(ForeignKey("barcode_labels.id"), nullable=True)
    
    # Physical properties (keeping for backward compatibility)
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
    minimum_order_quantity: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Relationships
    category = relationship("MaterialCategory", back_populates="materials")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder", foreign_keys=[po_id])
    po_line_item: Mapped[Optional["POLineItem"]] = relationship("POLineItem", foreign_keys=[po_line_item_id])
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", foreign_keys=[supplier_id])
    project: Mapped[Optional["Project"]] = relationship("Project", foreign_keys=[project_id])
    barcode: Mapped[Optional["BarcodeLabel"]] = relationship("BarcodeLabel", foreign_keys=[barcode_id])
    qa_inspector: Mapped[Optional["User"]] = relationship("User", foreign_keys=[qa_inspected_by])
    
    # Keep existing relationships for backward compatibility
    part_materials = relationship("PartMaterial", back_populates="material")
    supplier_materials = relationship("SupplierMaterial", back_populates="material")
    inventory = relationship("Inventory", back_populates="material")
    certifications = relationship("MaterialCertification", back_populates="material")
    order_items = relationship("OrderItem", back_populates="material")
    po_line_items = relationship(
        "POLineItem",
        back_populates="material",
        primaryjoin="Material.id == POLineItem.material_id"  # Explicitly specify join condition to avoid ambiguity
    )
    material_instances = relationship("MaterialInstance", back_populates="material")
    
    def __repr__(self) -> str:
        return f"<Material(id={self.id}, item_number='{self.item_number}', title='{self.title}')>"
