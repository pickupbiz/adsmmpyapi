"""Barcode tracking models for material traceability."""
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.inventory import Inventory


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


class BarcodeLabel(Base, TimestampMixin):
    """Barcode label master for tracking materials and inventory."""
    
    __tablename__ = "barcode_labels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Barcode details
    barcode_value: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    barcode_type: Mapped[BarcodeType] = mapped_column(
        Enum(BarcodeType),
        default=BarcodeType.CODE128,
        nullable=False
    )
    status: Mapped[BarcodeStatus] = mapped_column(
        Enum(BarcodeStatus),
        default=BarcodeStatus.ACTIVE,
        nullable=False
    )
    
    # Entity linking (polymorphic - can link to material, inventory, part, etc.)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'material', 'inventory', 'part'
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Additional tracking info
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Print tracking
    print_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_printed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Scan tracking
    scan_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_scanned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_scan_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Validity
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    scan_logs: Mapped[List["BarcodeScanLog"]] = relationship("BarcodeScanLog", back_populates="barcode_label")
    
    def __repr__(self) -> str:
        return f"<BarcodeLabel(id={self.id}, barcode='{self.barcode_value}', entity='{self.entity_type}:{self.entity_id}')>"


class BarcodeScanLog(Base, TimestampMixin):
    """Log of all barcode scans for audit and tracking."""
    
    __tablename__ = "barcode_scan_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    barcode_label_id: Mapped[int] = mapped_column(ForeignKey("barcode_labels.id"), nullable=False)
    scanned_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Scan details
    scan_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    scan_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    scan_device: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    scan_action: Mapped[str] = mapped_column(String(50), nullable=False)  # 'receipt', 'issue', 'transfer', 'inventory'
    
    # Result
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional context
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    barcode_label: Mapped["BarcodeLabel"] = relationship("BarcodeLabel", back_populates="scan_logs")
    scanned_by_user = relationship("User", foreign_keys=[scanned_by])
    
    def __repr__(self) -> str:
        return f"<BarcodeScanLog(id={self.id}, barcode_id={self.barcode_label_id}, action='{self.scan_action}')>"
