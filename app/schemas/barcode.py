"""Barcode Pydantic schemas."""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class BarcodeType(str, Enum):
    """Barcode type enumeration."""
    CODE128 = "code128"
    CODE39 = "code39"
    QR_CODE = "qr_code"
    DATA_MATRIX = "data_matrix"
    EAN13 = "ean13"
    UPC = "upc"


class BarcodeStatus(str, Enum):
    """Barcode status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    VOID = "void"


# Barcode Label Schemas
class BarcodeLabelBase(BaseModel):
    """Base barcode label schema."""
    barcode_value: str = Field(..., min_length=1, max_length=255)
    barcode_type: BarcodeType = BarcodeType.CODE128
    status: BarcodeStatus = BarcodeStatus.ACTIVE
    entity_type: str = Field(..., max_length=50)
    entity_id: int
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class BarcodeLabelCreate(BarcodeLabelBase):
    """Schema for creating a barcode label."""
    pass


class BarcodeLabelUpdate(BaseModel):
    """Schema for updating a barcode label."""
    barcode_type: Optional[BarcodeType] = None
    status: Optional[BarcodeStatus] = None
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class BarcodeLabelResponse(BarcodeLabelBase):
    """Schema for barcode label response."""
    id: int
    print_count: int
    last_printed_at: Optional[datetime]
    scan_count: int
    last_scanned_at: Optional[datetime]
    last_scan_location: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Barcode Scan Log Schemas
class BarcodeScanLogCreate(BaseModel):
    """Schema for creating a barcode scan log."""
    barcode_label_id: int
    scan_location: Optional[str] = Field(None, max_length=100)
    scan_device: Optional[str] = Field(None, max_length=100)
    scan_action: str = Field(..., max_length=50)
    is_successful: bool = True
    error_message: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class BarcodeScanLogResponse(BaseModel):
    """Schema for barcode scan log response."""
    id: int
    barcode_label_id: int
    scanned_by: int
    scan_timestamp: datetime
    scan_location: Optional[str]
    scan_device: Optional[str]
    scan_action: str
    is_successful: bool
    error_message: Optional[str]
    reference_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
