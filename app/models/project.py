"""Project and Bill of Materials (BOM) models."""
import enum
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean, DateTime, Date, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.material import Material
    from app.models.part import Part


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectPriority(str, enum.Enum):
    """Project priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BOMStatus(str, enum.Enum):
    """BOM status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RELEASED = "released"
    OBSOLETE = "obsolete"


class BOMType(str, enum.Enum):
    """BOM type enumeration."""
    ENGINEERING = "engineering"      # Design BOM
    MANUFACTURING = "manufacturing"  # Production BOM
    SERVICE = "service"              # Maintenance/repair BOM
    SALES = "sales"                  # Customer-facing BOM


class Project(Base, TimestampMixin):
    """Project model for tracking aerospace projects."""
    
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Project identification
    project_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    
    # Classification
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        default=ProjectStatus.PLANNING,
        nullable=False
    )
    priority: Mapped[ProjectPriority] = mapped_column(
        Enum(ProjectPriority),
        default=ProjectPriority.NORMAL,
        nullable=False
    )
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Customer/Contract info
    customer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contract_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timeline
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Budget
    budget: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Responsible parties
    project_manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Parent project for sub-projects
    parent_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    project_manager = relationship("User", foreign_keys=[project_manager_id])
    parent_project = relationship("Project", remote_side="Project.id", backref="sub_projects")
    boms: Mapped[List["BillOfMaterials"]] = relationship("BillOfMaterials", back_populates="project")
    material_requisitions: Mapped[List["MaterialRequisition"]] = relationship("MaterialRequisition", back_populates="project")
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, code='{self.code}', name='{self.name}')>"


class BillOfMaterials(Base, TimestampMixin):
    """Bill of Materials (BOM) header."""
    
    __tablename__ = "bill_of_materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # BOM identification
    bom_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    revision: Mapped[str] = mapped_column(String(10), default="A", nullable=False)
    
    # Classification
    bom_type: Mapped[BOMType] = mapped_column(
        Enum(BOMType),
        default=BOMType.MANUFACTURING,
        nullable=False
    )
    status: Mapped[BOMStatus] = mapped_column(
        Enum(BOMStatus),
        default=BOMStatus.DRAFT,
        nullable=False
    )
    
    # Links
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    part_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parts.id"), nullable=True)  # Top-level assembly
    
    # Effectivity
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Quantity
    base_quantity: Mapped[float] = mapped_column(Numeric(14, 4), default=1, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    
    # Approval tracking
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    released_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="boms")
    part = relationship("Part", foreign_keys=[part_id])
    approver = relationship("User", foreign_keys=[approved_by])
    releaser = relationship("User", foreign_keys=[released_by])
    items: Mapped[List["BOMItem"]] = relationship(
        "BOMItem", 
        back_populates="bom",
        cascade="all, delete-orphan",
        order_by="BOMItem.item_number",
        foreign_keys="[BOMItem.bom_id]"
    )
    
    def __repr__(self) -> str:
        return f"<BillOfMaterials(id={self.id}, bom_number='{self.bom_number}', rev='{self.revision}')>"


class BOMItem(Base, TimestampMixin):
    """Individual line item in a Bill of Materials."""
    
    __tablename__ = "bom_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bom_id: Mapped[int] = mapped_column(ForeignKey("bill_of_materials.id"), nullable=False)
    
    # Item identification
    item_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Line item number
    
    # Can be either material or part (sub-assembly)
    material_id: Mapped[Optional[int]] = mapped_column(ForeignKey("materials.id"), nullable=True)
    part_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parts.id"), nullable=True)
    child_bom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bill_of_materials.id"), nullable=True)  # For sub-assemblies
    
    # Quantity
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Waste/scrap factor (e.g., 1.05 for 5% expected waste)
    scrap_factor: Mapped[float] = mapped_column(Numeric(6, 4), default=1.0, nullable=False)
    
    # Optional reference designator (for electronics/assemblies)
    reference_designator: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Find number on drawing
    find_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Alternate/substitute allowed
    substitutes_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Operation/process step where item is consumed
    operation_sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    bom: Mapped["BillOfMaterials"] = relationship("BillOfMaterials", back_populates="items", foreign_keys=[bom_id])
    material = relationship("Material", foreign_keys=[material_id])
    part = relationship("Part", foreign_keys=[part_id])
    child_bom = relationship("BillOfMaterials", foreign_keys=[child_bom_id])
    
    @property
    def extended_quantity(self) -> float:
        """Calculate quantity including scrap factor."""
        return float(self.quantity) * float(self.scrap_factor)
    
    def __repr__(self) -> str:
        return f"<BOMItem(id={self.id}, bom_id={self.bom_id}, item={self.item_number})>"


class MaterialRequisition(Base, TimestampMixin):
    """Material requisition for project consumption."""
    
    __tablename__ = "material_requisitions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Requisition identification
    requisition_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Links
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    bom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bill_of_materials.id"), nullable=True)
    work_order: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Requestor
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    required_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)  # draft, pending, approved, issued, closed
    
    # Priority
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    
    # Approval
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Issue tracking
    issued_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="material_requisitions")
    bom = relationship("BillOfMaterials", foreign_keys=[bom_id])
    requestor = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    issuer = relationship("User", foreign_keys=[issued_by])
    items: Mapped[List["MaterialRequisitionItem"]] = relationship(
        "MaterialRequisitionItem",
        back_populates="requisition",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<MaterialRequisition(id={self.id}, number='{self.requisition_number}')>"


class MaterialRequisitionItem(Base, TimestampMixin):
    """Line item in a material requisition."""
    
    __tablename__ = "material_requisition_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    requisition_id: Mapped[int] = mapped_column(ForeignKey("material_requisitions.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    # Quantity
    quantity_requested: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_approved: Mapped[Optional[float]] = mapped_column(Numeric(14, 4), nullable=True)
    quantity_issued: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Inventory allocation
    inventory_id: Mapped[Optional[int]] = mapped_column(ForeignKey("inventory.id"), nullable=True)
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    requisition: Mapped["MaterialRequisition"] = relationship("MaterialRequisition", back_populates="items")
    material = relationship("Material", foreign_keys=[material_id])
    inventory = relationship("Inventory", foreign_keys=[inventory_id])
    
    def __repr__(self) -> str:
        return f"<MaterialRequisitionItem(id={self.id}, req_id={self.requisition_id}, material_id={self.material_id})>"
