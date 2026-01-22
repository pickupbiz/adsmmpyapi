"""Material Instance models for tracking individual materials with PO integration."""
import enum
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.material import Material
    from app.models.supplier import Supplier
    from app.models.purchase_order import PurchaseOrder, POLineItem, GRNLineItem
    from app.models.project import Project, BillOfMaterials


class MaterialLifecycleStatus(str, enum.Enum):
    """Material lifecycle status with PO context."""
    ORDERED = "ordered"           # On PO, awaiting delivery
    RECEIVED = "received"         # Physically received, pending inspection
    IN_INSPECTION = "in_inspection"  # Under QC inspection
    IN_STORAGE = "in_storage"     # Passed inspection, in warehouse
    RESERVED = "reserved"         # Reserved for a project/work order
    ISSUED = "issued"            # Issued to production
    IN_PRODUCTION = "in_production"  # Being used in manufacturing
    COMPLETED = "completed"       # Incorporated into finished goods
    REJECTED = "rejected"         # Failed inspection
    SCRAPPED = "scrapped"        # Written off/scrapped
    RETURNED = "returned"        # Returned to supplier


class MaterialCondition(str, enum.Enum):
    """Material condition classification."""
    NEW = "new"
    SERVICEABLE = "serviceable"
    UNSERVICEABLE = "unserviceable"
    OVERHAULED = "overhauled"
    REPAIRABLE = "repairable"
    SCRAP = "scrap"


class MaterialInstance(Base, TimestampMixin):
    """
    Individual material instance tracking with full PO integration.
    Each instance represents a physical material item with traceability.
    """
    
    __tablename__ = "material_instances"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Unique item identifier
    item_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Material master link
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    # PO Integration (source)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    po_line_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("po_line_items.id"), nullable=True)
    grn_line_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("grn_line_items.id"), nullable=True)
    
    # Supplier reference (from PO or direct)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    
    # Specification details
    specification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    revision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Quantity and units
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    issued_quantity: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Traceability
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    heat_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Status tracking
    lifecycle_status: Mapped[MaterialLifecycleStatus] = mapped_column(
        Enum(MaterialLifecycleStatus, values_callable=lambda x: [e.value for e in x]),
        default=MaterialLifecycleStatus.ORDERED,
        nullable=False,
        index=True
    )
    condition: Mapped[MaterialCondition] = mapped_column(
        Enum(MaterialCondition, values_callable=lambda x: [e.value for e in x]),
        default=MaterialCondition.NEW,
        nullable=False
    )
    
    # Important dates
    order_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    inspection_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    manufacture_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Location
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bin_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Certification/Compliance
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    certificate_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    inspection_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    inspection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # References
    po_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # PO number for quick lookup
    project_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # User tracking
    received_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    inspected_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    material: Mapped["Material"] = relationship("Material")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    po_line_item: Mapped[Optional["POLineItem"]] = relationship("POLineItem")
    grn_line_item: Mapped[Optional["GRNLineItem"]] = relationship("GRNLineItem")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier")
    received_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[received_by_id])
    inspected_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[inspected_by_id])
    
    allocations: Mapped[List["MaterialAllocation"]] = relationship(
        "MaterialAllocation",
        back_populates="material_instance",
        cascade="all, delete-orphan"
    )
    
    status_history: Mapped[List["MaterialStatusHistory"]] = relationship(
        "MaterialStatusHistory",
        back_populates="material_instance",
        cascade="all, delete-orphan",
        order_by="MaterialStatusHistory.created_at.desc()"
    )
    
    @property
    def available_quantity(self) -> float:
        """Get available quantity (total - reserved - issued)."""
        return max(0, float(self.quantity) - float(self.reserved_quantity) - float(self.issued_quantity))
    
    @property
    def is_available(self) -> bool:
        """Check if material is available for allocation."""
        return self.lifecycle_status == MaterialLifecycleStatus.IN_STORAGE and self.available_quantity > 0
    
    @property
    def is_expired(self) -> bool:
        """Check if material has expired."""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False
    
    def __repr__(self) -> str:
        return f"<MaterialInstance(id={self.id}, item_number='{self.item_number}', status='{self.lifecycle_status}')>"


class MaterialAllocation(Base, TimestampMixin):
    """
    Tracks material allocation to projects, work orders, or BOMs.
    Links material instances to where they are being used.
    """
    
    __tablename__ = "material_allocations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Material instance being allocated
    material_instance_id: Mapped[int] = mapped_column(ForeignKey("material_instances.id"), nullable=False)
    
    # Allocation target (one of these should be set)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    bom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bill_of_materials.id"), nullable=True)
    work_order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Allocation details
    allocation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    quantity_allocated: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_issued: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    quantity_returned: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_fulfilled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Dates
    allocation_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    required_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    issued_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # User tracking
    allocated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issued_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Priority
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1=highest, 10=lowest
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    material_instance: Mapped["MaterialInstance"] = relationship("MaterialInstance", back_populates="allocations")
    project: Mapped[Optional["Project"]] = relationship("Project")
    bom: Mapped[Optional["BillOfMaterials"]] = relationship("BillOfMaterials")
    allocated_by: Mapped["User"] = relationship("User", foreign_keys=[allocated_by_id])
    issued_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[issued_by_id])
    
    @property
    def outstanding_quantity(self) -> float:
        """Get quantity yet to be issued."""
        return max(0, float(self.quantity_allocated) - float(self.quantity_issued))
    
    def __repr__(self) -> str:
        return f"<MaterialAllocation(id={self.id}, allocation_number='{self.allocation_number}')>"


class MaterialStatusHistory(Base, TimestampMixin):
    """
    Audit trail for material lifecycle status changes.
    Tracks who, when, and why status changed.
    """
    
    __tablename__ = "material_status_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    material_instance_id: Mapped[int] = mapped_column(ForeignKey("material_instances.id"), nullable=False)
    
    # Status transition
    from_status: Mapped[Optional[MaterialLifecycleStatus]] = mapped_column(
        Enum(MaterialLifecycleStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    to_status: Mapped[MaterialLifecycleStatus] = mapped_column(
        Enum(MaterialLifecycleStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # User who made the change
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Reference information
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "PO", "GRN", "ISSUE"
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Details
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    material_instance: Mapped["MaterialInstance"] = relationship("MaterialInstance", back_populates="status_history")
    changed_by: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<MaterialStatusHistory(id={self.id}, from={self.from_status}, to={self.to_status})>"


class BOMSourceTracking(Base, TimestampMixin):
    """
    Tracks PO sourcing information for BOM items.
    Links BOM requirements to actual POs and material receipts.
    """
    
    __tablename__ = "bom_source_tracking"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # BOM reference
    bom_id: Mapped[int] = mapped_column(ForeignKey("bill_of_materials.id"), nullable=False)
    bom_item_id: Mapped[int] = mapped_column(ForeignKey("bom_items.id"), nullable=False)
    
    # Source PO
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    po_line_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("po_line_items.id"), nullable=True)
    
    # Actual material used
    material_instance_id: Mapped[Optional[int]] = mapped_column(ForeignKey("material_instances.id"), nullable=True)
    
    # Quantity tracking
    quantity_required: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_allocated: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    quantity_consumed: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Status
    is_fulfilled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Dates
    required_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    allocated_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    consumed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    bom: Mapped["BillOfMaterials"] = relationship("BillOfMaterials")
    bom_item: Mapped["BOMItem"] = relationship("BOMItem")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    po_line_item: Mapped[Optional["POLineItem"]] = relationship("POLineItem")
    material_instance: Mapped[Optional["MaterialInstance"]] = relationship("MaterialInstance")
    
    @property
    def shortage_quantity(self) -> float:
        """Get quantity still needed."""
        return max(0, float(self.quantity_required) - float(self.quantity_allocated))
    
    def __repr__(self) -> str:
        return f"<BOMSourceTracking(id={self.id}, bom_id={self.bom_id})>"
