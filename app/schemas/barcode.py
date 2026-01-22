"""Comprehensive barcode Pydantic schemas with PO integration."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


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
    CONSUMED = "consumed"


class BarcodeEntityType(str, Enum):
    """Entity types that can have barcodes."""
    RAW_MATERIAL = "raw_material"
    WIP = "wip"
    FINISHED_GOODS = "finished_goods"
    MATERIAL_INSTANCE = "material_instance"
    PO_LINE_ITEM = "po_line_item"
    GRN_LINE_ITEM = "grn_line_item"
    INVENTORY = "inventory"
    PART = "part"


class TraceabilityStage(str, Enum):
    """Material traceability stage."""
    ORDERED = "ordered"
    RECEIVED = "received"
    INSPECTED = "inspected"
    IN_STORAGE = "in_storage"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    CONSUMED = "consumed"
    SHIPPED = "shipped"


# =============================================================================
# Barcode Label Schemas
# =============================================================================

class BarcodeLabelBase(BaseModel):
    """Base barcode label schema."""
    barcode_type: BarcodeType = BarcodeType.CODE128
    entity_type: BarcodeEntityType
    entity_id: int
    traceability_stage: TraceabilityStage = TraceabilityStage.RECEIVED
    
    # PO Integration
    purchase_order_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    grn_id: Optional[int] = None
    material_instance_id: Optional[int] = None
    po_number: Optional[str] = Field(None, max_length=50)
    grn_number: Optional[str] = Field(None, max_length=50)
    
    # Material Details
    material_id: Optional[int] = None
    material_part_number: Optional[str] = Field(None, max_length=100)
    material_name: Optional[str] = Field(None, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    
    # Batch/Lot
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    heat_number: Optional[str] = Field(None, max_length=100)
    
    # Quantity
    initial_quantity: Optional[float] = Field(None, ge=0)
    current_quantity: Optional[float] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    
    # Supplier
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = Field(None, max_length=200)
    
    # Dates
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    received_date: Optional[date] = None
    
    # Location
    current_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    
    # References
    project_reference: Optional[str] = Field(None, max_length=100)
    work_order_reference: Optional[str] = Field(None, max_length=100)
    
    # Validity
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    notes: Optional[str] = None


class BarcodeLabelCreate(BarcodeLabelBase):
    """Schema for creating a barcode label."""
    # Barcode value can be auto-generated or provided
    barcode_value: Optional[str] = Field(None, max_length=255)
    auto_generate: bool = True  # If True, auto-generate barcode value
    
    # Parent barcode for traceability chain
    parent_barcode_id: Optional[int] = None


class BarcodeLabelFromPO(BaseModel):
    """Schema for creating barcode from PO line item."""
    po_line_item_id: int
    grn_line_item_id: Optional[int] = None
    
    # Batch/Lot info (override or from GRN)
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    heat_number: Optional[str] = Field(None, max_length=100)
    
    # Quantity (defaults to PO line quantity)
    quantity: Optional[float] = Field(None, ge=0)
    
    # Dates
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    
    # Location
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    
    # Barcode type
    barcode_type: BarcodeType = BarcodeType.QR_CODE
    
    notes: Optional[str] = None


class BarcodeLabelUpdate(BaseModel):
    """Schema for updating a barcode label."""
    status: Optional[BarcodeStatus] = None
    traceability_stage: Optional[TraceabilityStage] = None
    
    current_quantity: Optional[float] = Field(None, ge=0)
    current_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    
    project_reference: Optional[str] = Field(None, max_length=100)
    work_order_reference: Optional[str] = Field(None, max_length=100)
    
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class BarcodeLabelResponse(BarcodeLabelBase):
    """Schema for barcode label response."""
    id: int
    barcode_value: str
    status: BarcodeStatus
    
    # QR data
    qr_data: Optional[Dict[str, Any]] = None
    
    # Traceability
    parent_barcode_id: Optional[int] = None
    
    # Tracking
    print_count: int
    last_printed_at: Optional[datetime]
    scan_count: int
    last_scanned_at: Optional[datetime]
    last_scan_location: Optional[str]
    last_scan_action: Optional[str]
    
    # Computed
    is_valid: bool
    is_fully_consumed: bool
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BarcodeLabelDetailResponse(BarcodeLabelResponse):
    """Detailed barcode response with related data."""
    # PO details
    po_status: Optional[str] = None
    
    # Material details
    material_type: Optional[str] = None
    
    # Supplier details
    supplier_status: Optional[str] = None
    
    # Traceability chain
    parent_barcode_value: Optional[str] = None
    child_barcode_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Barcode Scan Schemas
# =============================================================================

class BarcodeScanRequest(BaseModel):
    """Schema for scanning a barcode."""
    barcode_value: str = Field(..., min_length=1, max_length=255)
    scan_action: str = Field(..., max_length=50)  # 'po_receipt', 'inspection', 'issue', 'wip_start', etc.
    
    # Location
    scan_location: Optional[str] = Field(None, max_length=100)
    scan_device: Optional[str] = Field(None, max_length=100)
    
    # Quantity (for partial operations)
    quantity: Optional[float] = Field(None, ge=0)
    
    # PO Context (for receipt validation)
    purchase_order_id: Optional[int] = None
    grn_id: Optional[int] = None
    
    # Location change
    new_location: Optional[str] = Field(None, max_length=100)
    new_bin: Optional[str] = Field(None, max_length=50)
    
    # Reference
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    
    notes: Optional[str] = None


class BarcodeScanByQRRequest(BaseModel):
    """Schema for scanning via QR code data."""
    qr_data: str  # JSON string or base64 encoded
    scan_action: str = Field(..., max_length=50)
    scan_location: Optional[str] = Field(None, max_length=100)
    scan_device: Optional[str] = Field(None, max_length=100)
    quantity: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class ScanToReceiveRequest(BaseModel):
    """Schema for scan-to-receive against PO."""
    barcode_value: str = Field(..., min_length=1)
    purchase_order_id: int
    po_line_item_id: int
    grn_id: Optional[int] = None
    
    # Receipt details
    quantity_received: float = Field(..., gt=0)
    
    # Location
    storage_location: str = Field(..., max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    
    # Validation
    validate_po: bool = True  # Validate barcode matches PO details
    
    notes: Optional[str] = None


class BarcodeScanLogCreate(BaseModel):
    """Schema for creating a barcode scan log."""
    barcode_label_id: int
    scan_action: str = Field(..., max_length=50)
    
    scan_location: Optional[str] = Field(None, max_length=100)
    scan_device: Optional[str] = Field(None, max_length=100)
    
    purchase_order_id: Optional[int] = None
    grn_id: Optional[int] = None
    
    quantity_scanned: Optional[float] = None
    
    location_from: Optional[str] = Field(None, max_length=100)
    location_to: Optional[str] = Field(None, max_length=100)
    
    is_successful: bool = True
    error_message: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    
    notes: Optional[str] = None


class BarcodeScanLogResponse(BaseModel):
    """Schema for barcode scan log response."""
    id: int
    barcode_label_id: int
    scanned_by: int
    scanned_by_name: Optional[str] = None
    
    scan_timestamp: datetime
    scan_location: Optional[str]
    scan_device: Optional[str]
    scan_action: str
    
    purchase_order_id: Optional[int]
    grn_id: Optional[int]
    
    quantity_scanned: Optional[float]
    quantity_before: Optional[float]
    quantity_after: Optional[float]
    
    status_before: Optional[str]
    status_after: Optional[str]
    stage_before: Optional[str]
    stage_after: Optional[str]
    
    location_from: Optional[str]
    location_to: Optional[str]
    
    is_successful: bool
    error_message: Optional[str]
    validation_result: Optional[Dict[str, Any]]
    
    reference_type: Optional[str]
    reference_number: Optional[str]
    
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Barcode Validation Schemas
# =============================================================================

class BarcodeValidationRequest(BaseModel):
    """Schema for validating a barcode against PO."""
    barcode_value: str
    purchase_order_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    expected_material_id: Optional[int] = None
    expected_quantity: Optional[float] = None


class BarcodeValidationResult(BaseModel):
    """Schema for barcode validation result."""
    is_valid: bool
    barcode_found: bool
    barcode_active: bool
    
    # PO validation
    po_match: bool = False
    material_match: bool = False
    quantity_valid: bool = False
    not_expired: bool = False
    
    # Details
    barcode_id: Optional[int] = None
    barcode_status: Optional[str] = None
    po_number: Optional[str] = None
    material_part_number: Optional[str] = None
    current_quantity: Optional[float] = None
    
    # Errors/Warnings
    errors: List[str] = []
    warnings: List[str] = []
    
    # Full validation details
    checks: Dict[str, bool] = {}


# =============================================================================
# Barcode Generation Schemas
# =============================================================================

class GenerateBarcodeRequest(BaseModel):
    """Schema for generating a new barcode."""
    entity_type: BarcodeEntityType
    entity_id: int
    barcode_type: BarcodeType = BarcodeType.QR_CODE
    
    # PO reference (for raw materials)
    po_number: Optional[str] = None
    po_line_item_id: Optional[int] = None
    
    # Material details
    material_id: Optional[int] = None
    material_part_number: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    
    # Batch/Lot
    lot_number: Optional[str] = None
    batch_number: Optional[str] = None
    serial_number: Optional[str] = None
    heat_number: Optional[str] = None
    
    # Quantity
    quantity: Optional[float] = None
    unit_of_measure: Optional[str] = None
    
    # Supplier
    supplier_name: Optional[str] = None
    
    # Dates
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    
    # Location
    storage_location: Optional[str] = None
    bin_number: Optional[str] = None
    
    # Traceability
    parent_barcode_id: Optional[int] = None
    work_order_reference: Optional[str] = None


class GenerateBarcodeResponse(BaseModel):
    """Schema for generated barcode response."""
    barcode_id: int
    barcode_value: str
    barcode_type: BarcodeType
    
    # QR data (for QR codes)
    qr_data: Optional[Dict[str, Any]] = None
    qr_data_encoded: Optional[str] = None  # Base64 encoded for embedding
    
    # Images (base64 encoded)
    barcode_image_base64: Optional[str] = None
    qr_image_base64: Optional[str] = None
    
    # Print URLs
    barcode_print_url: Optional[str] = None
    qr_print_url: Optional[str] = None


class BulkGenerateBarcodeRequest(BaseModel):
    """Schema for bulk barcode generation."""
    po_line_item_ids: List[int]
    barcode_type: BarcodeType = BarcodeType.QR_CODE
    auto_print: bool = False


class BulkGenerateBarcodeResponse(BaseModel):
    """Schema for bulk generated barcodes response."""
    total_requested: int
    total_generated: int
    barcodes: List[GenerateBarcodeResponse]
    errors: List[str] = []


# =============================================================================
# WIP Barcode Schemas
# =============================================================================

class CreateWIPBarcodeRequest(BaseModel):
    """Schema for creating a WIP barcode from raw material."""
    parent_barcode_id: int  # Raw material barcode
    work_order_reference: str = Field(..., max_length=100)
    quantity_used: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    
    # Optional details
    operation: Optional[str] = Field(None, max_length=100)  # e.g., "Machining", "Heat Treatment"
    station: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class CreateFinishedGoodsBarcodeRequest(BaseModel):
    """Schema for creating finished goods barcode."""
    parent_barcode_ids: List[int]  # WIP or raw material barcodes used
    part_number: str = Field(..., max_length=100)
    part_name: str = Field(..., max_length=200)
    serial_number: str = Field(..., max_length=100)
    work_order_reference: str = Field(..., max_length=100)
    
    # Optional
    project_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


# =============================================================================
# Barcode Template Schemas
# =============================================================================

class BarcodeTemplateBase(BaseModel):
    """Base schema for barcode template."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    # Using str to avoid enum issues, validated values: 'code128', 'code39', 'qr_code', 'data_matrix', 'ean13', 'upc'
    barcode_type: str = Field(..., max_length=50)
    # Using str to avoid enum issues, validated values: 'raw_material', 'wip', 'finished_goods', etc.
    entity_type: str = Field(..., max_length=50)
    format_pattern: str = Field(..., max_length=255)
    prefix: str = Field(..., max_length=20)
    sequence_start: int = Field(default=1, ge=1)
    sequence_padding: int = Field(default=5, ge=1, le=10)
    qr_data_template: Optional[Dict[str, Any]] = None
    include_po_reference: bool = True
    include_material_details: bool = True
    include_lot_info: bool = True
    include_dates: bool = True
    include_supplier: bool = False
    is_active: bool = True


class BarcodeTemplateCreate(BarcodeTemplateBase):
    """Schema for creating barcode template."""
    pass


class BarcodeTemplateUpdate(BaseModel):
    """Schema for updating barcode template."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    format_pattern: Optional[str] = Field(None, max_length=255)
    prefix: Optional[str] = Field(None, max_length=20)
    qr_data_template: Optional[Dict[str, Any]] = None
    include_po_reference: Optional[bool] = None
    include_material_details: Optional[bool] = None
    include_lot_info: Optional[bool] = None
    include_dates: Optional[bool] = None
    include_supplier: Optional[bool] = None
    is_active: Optional[bool] = None


class BarcodeTemplateResponse(BarcodeTemplateBase):
    """Schema for barcode template response."""
    id: int
    sequence_current: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Traceability Schemas
# =============================================================================

class TraceabilityChainItem(BaseModel):
    """Single item in traceability chain."""
    barcode_id: int
    barcode_value: str
    entity_type: BarcodeEntityType
    traceability_stage: TraceabilityStage
    po_number: Optional[str]
    material_part_number: Optional[str]
    lot_number: Optional[str]
    quantity: Optional[float]
    created_at: datetime


class TraceabilityChainResponse(BaseModel):
    """Full traceability chain for a barcode."""
    barcode_id: int
    barcode_value: str
    chain_length: int
    chain: List[TraceabilityChainItem]
    
    # Source PO info
    source_po_number: Optional[str] = None
    source_supplier: Optional[str] = None
    
    # End product info
    finished_goods_serial: Optional[str] = None


class BarcodeSearchRequest(BaseModel):
    """Schema for searching barcodes."""
    barcode_value: Optional[str] = None
    po_number: Optional[str] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    heat_number: Optional[str] = None
    material_part_number: Optional[str] = None
    entity_type: Optional[BarcodeEntityType] = None
    traceability_stage: Optional[TraceabilityStage] = None
    status: Optional[BarcodeStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


# =============================================================================
# Report Schemas
# =============================================================================

class BarcodeSummaryByStage(BaseModel):
    """Summary of barcodes by traceability stage."""
    stage: TraceabilityStage
    count: int
    total_quantity: float


class BarcodeSummaryByPO(BaseModel):
    """Summary of barcodes by PO."""
    po_number: str
    po_id: int
    total_barcodes: int
    received_count: int
    in_storage_count: int
    in_production_count: int
    completed_count: int


class BarcodeActivityReport(BaseModel):
    """Barcode activity report."""
    period_start: datetime
    period_end: datetime
    total_scans: int
    successful_scans: int
    failed_scans: int
    scans_by_action: Dict[str, int]
    top_scanned_barcodes: List[Dict[str, Any]]
