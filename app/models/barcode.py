"""Barcode tracking models with PO integration for material traceability."""
import enum
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean, DateTime, Integer, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.inventory import Inventory
    from app.models.user import User
    from app.models.supplier import Supplier
    from app.models.purchase_order import PurchaseOrder, POLineItem, GoodsReceiptNote
    from app.models.material_instance import MaterialInstance


class BarcodeType(str, enum.Enum):
    """Barcode type enumeration."""
    CODE128 = "code128"
    CODE39 = "code39"
    QR_CODE = "qr_code"
    DATA_MATRIX = "data_matrix"
    EAN13 = "ean13"
    UPC = "upc"


class BarcodeStatus(str, enum.Enum):
    """Barcode status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    VOID = "void"
    CONSUMED = "consumed"  # Material has been fully used


class BarcodeEntityType(str, enum.Enum):
    """Entity types that can have barcodes."""
    RAW_MATERIAL = "raw_material"
    WIP = "wip"  # Work in Progress
    FINISHED_GOODS = "finished_goods"
    MATERIAL_INSTANCE = "material_instance"
    PO_LINE_ITEM = "po_line_item"
    GRN_LINE_ITEM = "grn_line_item"
    INVENTORY = "inventory"
    PART = "part"


class TraceabilityStage(str, enum.Enum):
    """Material traceability stage."""
    ORDERED = "ordered"           # PO created
    RECEIVED = "received"         # GRN created
    INSPECTED = "inspected"       # QC passed
    IN_STORAGE = "in_storage"     # Raw material in warehouse
    IN_PRODUCTION = "in_production"  # WIP
    COMPLETED = "completed"       # Finished goods
    CONSUMED = "consumed"         # Used in assembly
    SHIPPED = "shipped"           # Dispatched


class BarcodeLabel(Base, TimestampMixin):
    """
    Enhanced barcode label with PO integration and full traceability.
    
    Supports:
    - Unique barcode per material batch/unit
    - PO reference embedding
    - QR code with full material details
    - WIP and finished goods tracking
    - Complete traceability chain back to PO
    """
    
    __tablename__ = "barcode_labels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Barcode identification
    barcode_value: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    barcode_type: Mapped[BarcodeType] = mapped_column(
        Enum(BarcodeType, values_callable=lambda x: [e.value for e in x]),
        default=BarcodeType.CODE128,
        nullable=False
    )
    status: Mapped[BarcodeStatus] = mapped_column(
        Enum(BarcodeStatus, values_callable=lambda x: [e.value for e in x]),
        default=BarcodeStatus.ACTIVE,
        nullable=False
    )
    
    # Entity linking (what this barcode represents)
    entity_type: Mapped[BarcodeEntityType] = mapped_column(
        Enum(BarcodeEntityType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Traceability stage
    traceability_stage: Mapped[TraceabilityStage] = mapped_column(
        Enum(TraceabilityStage, values_callable=lambda x: [e.value for e in x]),
        default=TraceabilityStage.RECEIVED,
        nullable=False
    )
    
    # === PO INTEGRATION ===
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True, index=True)
    po_line_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("po_line_items.id"), nullable=True)
    grn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("goods_receipt_notes.id"), nullable=True)
    material_instance_id: Mapped[Optional[int]] = mapped_column(ForeignKey("material_instances.id"), nullable=True, index=True)
    
    # PO reference for quick lookup (denormalized for performance)
    po_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    grn_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # === MATERIAL DETAILS ===
    material_id: Mapped[Optional[int]] = mapped_column(ForeignKey("materials.id"), nullable=True)
    material_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    material_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    specification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # === BATCH/LOT TRACKING ===
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    heat_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # === QUANTITY TRACKING ===
    initial_quantity: Mapped[Optional[float]] = mapped_column(nullable=True)
    current_quantity: Mapped[Optional[float]] = mapped_column(nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # === SUPPLIER INFO ===
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # === DATES ===
    manufacture_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # === QR CODE DATA (JSON for rich mobile scanning) ===
    qr_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Full encoded data for QR
    
    # === TRACEABILITY CHAIN ===
    parent_barcode_id: Mapped[Optional[int]] = mapped_column(ForeignKey("barcode_labels.id"), nullable=True)
    # Links WIP/FG barcode back to raw material barcode
    
    # === PRINT TRACKING ===
    print_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_printed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # === SCAN TRACKING ===
    scan_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_scanned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_scan_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_scan_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # === VALIDITY ===
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # === LOCATION ===
    current_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bin_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # === PROJECT/WORK ORDER REFERENCE ===
    project_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # === RELATIONSHIPS ===
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    po_line_item: Mapped[Optional["POLineItem"]] = relationship("POLineItem", foreign_keys=[po_line_item_id])
    goods_receipt: Mapped[Optional["GoodsReceiptNote"]] = relationship("GoodsReceiptNote", foreign_keys=[grn_id])
    material_instance: Mapped[Optional["MaterialInstance"]] = relationship("MaterialInstance", foreign_keys=[material_instance_id])
    material: Mapped[Optional["Material"]] = relationship("Material", foreign_keys=[material_id])
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", foreign_keys=[supplier_id])
    
    # Self-referential for traceability chain
    parent_barcode: Mapped[Optional["BarcodeLabel"]] = relationship(
        "BarcodeLabel", 
        remote_side=[id],
        foreign_keys=[parent_barcode_id],
        backref="child_barcodes"
    )
    
    scan_logs: Mapped[List["BarcodeScanLog"]] = relationship(
        "BarcodeScanLog", 
        back_populates="barcode_label",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_valid(self) -> bool:
        """Check if barcode is currently valid."""
        if self.status != BarcodeStatus.ACTIVE:
            return False
        now = datetime.utcnow()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.expiry_date and date.today() > self.expiry_date:
            return False
        return True
    
    @property
    def is_fully_consumed(self) -> bool:
        """Check if material is fully consumed."""
        if self.current_quantity is not None and self.current_quantity <= 0:
            return True
        return self.status == BarcodeStatus.CONSUMED
    
    def get_traceability_chain(self) -> List["BarcodeLabel"]:
        """Get full traceability chain from this barcode back to original PO."""
        chain = [self]
        current = self
        while current.parent_barcode:
            chain.append(current.parent_barcode)
            current = current.parent_barcode
        return chain
    
    def __repr__(self) -> str:
        return f"<BarcodeLabel(id={self.id}, barcode='{self.barcode_value}', po='{self.po_number}', stage='{self.traceability_stage}')>"


class BarcodeScanLog(Base, TimestampMixin):
    """Log of all barcode scans for audit and tracking with PO context."""
    
    __tablename__ = "barcode_scan_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    barcode_label_id: Mapped[int] = mapped_column(ForeignKey("barcode_labels.id"), nullable=False)
    scanned_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Scan details
    scan_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    scan_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    scan_device: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    scan_action: Mapped[str] = mapped_column(String(50), nullable=False)  # 'po_receipt', 'inspection', 'issue', 'wip_start', 'wip_complete', 'transfer'
    
    # PO Context
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True)
    grn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("goods_receipt_notes.id"), nullable=True)
    
    # Quantity tracking for partial operations
    quantity_scanned: Mapped[Optional[float]] = mapped_column(nullable=True)
    quantity_before: Mapped[Optional[float]] = mapped_column(nullable=True)
    quantity_after: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Status change
    status_before: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status_after: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stage_before: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stage_after: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Location change
    location_from: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Result
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Detailed validation results
    
    # References
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'PO', 'GRN', 'WO'
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Client info
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    barcode_label: Mapped["BarcodeLabel"] = relationship("BarcodeLabel", back_populates="scan_logs")
    scanned_by_user: Mapped["User"] = relationship("User", foreign_keys=[scanned_by])
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    goods_receipt: Mapped[Optional["GoodsReceiptNote"]] = relationship("GoodsReceiptNote", foreign_keys=[grn_id])
    
    def __repr__(self) -> str:
        return f"<BarcodeScanLog(id={self.id}, barcode_id={self.barcode_label_id}, action='{self.scan_action}', success={self.is_successful})>"


class BarcodeTemplate(Base, TimestampMixin):
    """Templates for barcode generation with configurable formats."""
    
    __tablename__ = "barcode_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Template settings - using String to avoid enum issues
    # Values: 'code128', 'code39', 'qr_code', 'data_matrix', 'ean13', 'upc'
    barcode_type: Mapped[str] = mapped_column(String(50), default='code128', nullable=False)
    # Values: 'raw_material', 'wip', 'finished_goods', 'material_instance', etc.
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Format template (e.g., "{prefix}-{po_number}-{material_id}-{lot}-{seq}")
    format_pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Sequence settings
    sequence_start: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sequence_current: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sequence_padding: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # Zero padding
    
    # QR data template (JSON structure for QR codes)
    qr_data_template: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Include fields in barcode
    include_po_reference: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_material_details: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_lot_info: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_dates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_supplier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<BarcodeTemplate(id={self.id}, name='{self.name}', type='{self.barcode_type}')>"
