"""Enhanced Purchase Order models with approval workflow and material lifecycle tracking."""
import enum
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Enum, ForeignKey, Boolean, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.supplier import Supplier
    from app.models.material import Material
    from app.models.inventory import Inventory


class POStatus(str, enum.Enum):
    """Purchase Order status enumeration."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class POPriority(str, enum.Enum):
    """Purchase Order priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    AOG = "aog"  # Aircraft on Ground - highest priority


class ApprovalAction(str, enum.Enum):
    """Approval action types."""
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"  # Returned for revision
    CANCELLED = "cancelled"


class MaterialStage(str, enum.Enum):
    """Material lifecycle stage tracking."""
    ON_ORDER = "on_order"           # PO created, awaiting delivery
    RAW_MATERIAL = "raw_material"   # Received and in raw material inventory
    IN_INSPECTION = "in_inspection" # Under QC inspection
    WIP = "wip"                     # Work in Progress
    FINISHED_GOODS = "finished_goods"  # Completed and ready for use/sale
    CONSUMED = "consumed"           # Used in production
    SCRAPPED = "scrapped"           # Rejected/scrapped


class GRNStatus(str, enum.Enum):
    """Goods Receipt Note status."""
    DRAFT = "draft"
    PENDING_INSPECTION = "pending_inspection"
    INSPECTION_PASSED = "inspection_passed"
    INSPECTION_FAILED = "inspection_failed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"  # Partially accepted


class PurchaseOrder(Base, TimestampMixin):
    """Enhanced Purchase Order model with approval workflow."""
    
    __tablename__ = "purchase_orders"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Supplier relationship
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    
    # User relationships
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Status and priority
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, values_callable=lambda x: [e.value for e in x]),
        default=POStatus.DRAFT,
        nullable=False
    )
    priority: Mapped[POPriority] = mapped_column(
        Enum(POPriority, values_callable=lambda x: [e.value for e in x]),
        default=POPriority.NORMAL,
        nullable=False
    )
    
    # Important dates
    po_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    required_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approved_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ordered_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Financial
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approval_threshold: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Shipping information
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # References
    requisition_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Compliance
    requires_certification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_inspection: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Terms
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "Net 30"
    delivery_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "FOB Origin"
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Not visible to supplier
    
    # Revision tracking
    revision_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", foreign_keys=[supplier_id])
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_id])
    
    line_items: Mapped[List["POLineItem"]] = relationship(
        "POLineItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="POLineItem.line_number"
    )
    
    approval_history: Mapped[List["POApprovalHistory"]] = relationship(
        "POApprovalHistory",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="POApprovalHistory.created_at.desc()"
    )
    
    goods_receipts: Mapped[List["GoodsReceiptNote"]] = relationship(
        "GoodsReceiptNote",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )
    
    def calculate_totals(self) -> None:
        """Calculate PO totals from line items."""
        self.subtotal = sum(item.total_price for item in self.line_items if item.total_price)
        self.total_amount = float(self.subtotal) + float(self.tax_amount) + float(self.shipping_cost) - float(self.discount_amount)
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number='{self.po_number}', status='{self.status}')>"


class POLineItem(Base, TimestampMixin):
    """Purchase Order line item with material lifecycle tracking."""
    
    __tablename__ = "po_line_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    
    # Line identification
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Quantity tracking
    quantity_ordered: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    quantity_accepted: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    quantity_rejected: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Pricing
    unit_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    
    # Material lifecycle stage
    material_stage: Mapped[MaterialStage] = mapped_column(
        Enum(MaterialStage, values_callable=lambda x: [e.value for e in x]),
        default=MaterialStage.ON_ORDER,
        nullable=False
    )
    
    # Delivery
    required_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    promised_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Specifications
    specification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    revision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Compliance
    requires_certification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    certification_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_inspection: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inspection_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="line_items")
    material: Mapped["Material"] = relationship("Material", back_populates="po_line_items")
    
    grn_items: Mapped[List["GRNLineItem"]] = relationship(
        "GRNLineItem",
        back_populates="po_line_item",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_fully_received(self) -> bool:
        """Check if line item is fully received."""
        return float(self.quantity_received) >= float(self.quantity_ordered)
    
    @property
    def outstanding_quantity(self) -> float:
        """Get quantity yet to be received."""
        return max(0, float(self.quantity_ordered) - float(self.quantity_received))
    
    def calculate_total(self) -> None:
        """Calculate line total with discount."""
        subtotal = float(self.quantity_ordered) * float(self.unit_price)
        discount = subtotal * (float(self.discount_percent) / 100)
        self.total_price = subtotal - discount
    
    def __repr__(self) -> str:
        return f"<POLineItem(id={self.id}, po_id={self.purchase_order_id}, line={self.line_number})>"


class POApprovalHistory(Base, TimestampMixin):
    """Tracks approval history and audit trail for Purchase Orders."""
    
    __tablename__ = "po_approval_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Action details
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # Status transition
    from_status: Mapped[Optional[POStatus]] = mapped_column(
        Enum(POStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    to_status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # Details
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Snapshot of PO at approval time
    po_total_at_action: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    po_revision_at_action: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # IP tracking for audit
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="approval_history")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<POApprovalHistory(id={self.id}, po_id={self.purchase_order_id}, action='{self.action}')>"


class GoodsReceiptNote(Base, TimestampMixin):
    """Goods Receipt Note for tracking material receiving against PO."""
    
    __tablename__ = "goods_receipt_notes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    grn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    received_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    inspected_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Status
    status: Mapped[GRNStatus] = mapped_column(
        Enum(GRNStatus, values_callable=lambda x: [e.value for e in x]),
        default=GRNStatus.DRAFT,
        nullable=False
    )
    
    # Dates
    receipt_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    inspection_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Shipping details
    delivery_note_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Documentation
    packing_slip_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    coc_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Certificate of Conformance
    mtr_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Mill Test Report
    
    # Storage
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inspection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="goods_receipts")
    received_by: Mapped["User"] = relationship("User", foreign_keys=[received_by_id])
    inspected_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[inspected_by_id])
    
    line_items: Mapped[List["GRNLineItem"]] = relationship(
        "GRNLineItem",
        back_populates="goods_receipt",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<GoodsReceiptNote(id={self.id}, grn_number='{self.grn_number}')>"


class GRNLineItem(Base, TimestampMixin):
    """Goods Receipt Note line item - tracks received quantities per PO line."""
    
    __tablename__ = "grn_line_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    goods_receipt_id: Mapped[int] = mapped_column(ForeignKey("goods_receipt_notes.id"), nullable=False)
    po_line_item_id: Mapped[int] = mapped_column(ForeignKey("po_line_items.id"), nullable=False)
    
    # Quantities
    quantity_received: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_accepted: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    quantity_rejected: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Batch/Lot tracking
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_numbers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array for serialized items
    heat_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dates
    manufacture_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Inspection
    inspection_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # passed, failed, pending
    inspection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Rejection details
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ncr_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Non-Conformance Report
    
    # Storage
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bin_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Link to inventory (created after acceptance)
    inventory_id: Mapped[Optional[int]] = mapped_column(ForeignKey("inventory.id"), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    goods_receipt: Mapped["GoodsReceiptNote"] = relationship("GoodsReceiptNote", back_populates="line_items")
    po_line_item: Mapped["POLineItem"] = relationship("POLineItem", back_populates="grn_items")
    inventory: Mapped[Optional["Inventory"]] = relationship("Inventory")
    
    def __repr__(self) -> str:
        return f"<GRNLineItem(id={self.id}, grn_id={self.goods_receipt_id}, qty={self.quantity_received})>"
