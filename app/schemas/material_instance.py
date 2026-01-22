"""Pydantic schemas for Material Instance management with PO integration."""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class MaterialLifecycleStatus(str, Enum):
    """Material lifecycle status with PO context."""
    ORDERED = "ordered"
    RECEIVED = "received"
    IN_INSPECTION = "in_inspection"
    IN_STORAGE = "in_storage"
    RESERVED = "reserved"
    ISSUED = "issued"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SCRAPPED = "scrapped"
    RETURNED = "returned"


class MaterialCondition(str, Enum):
    """Material condition classification."""
    NEW = "new"
    SERVICEABLE = "serviceable"
    UNSERVICEABLE = "unserviceable"
    OVERHAULED = "overhauled"
    REPAIRABLE = "repairable"
    SCRAP = "scrap"


# =============================================================================
# Material Instance Schemas
# =============================================================================

class MaterialInstanceBase(BaseModel):
    """Base schema for material instance."""
    title: str = Field(..., min_length=1, max_length=200)
    material_id: int
    specification: Optional[str] = Field(None, max_length=200)
    revision: Optional[str] = Field(None, max_length=20)
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    unit_cost: Optional[float] = Field(None, ge=0)
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    heat_number: Optional[str] = Field(None, max_length=100)
    condition: MaterialCondition = MaterialCondition.NEW
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    certificate_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class MaterialInstanceCreate(MaterialInstanceBase):
    """Schema for creating a material instance."""
    # Can be created from PO/GRN or directly
    purchase_order_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    grn_line_item_id: Optional[int] = None
    supplier_id: Optional[int] = None
    order_date: Optional[date] = None
    received_date: Optional[date] = None


class MaterialInstanceFromGRN(BaseModel):
    """Schema for creating material instance from GRN receipt."""
    grn_line_item_id: int
    title: str = Field(..., min_length=1, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    revision: Optional[str] = Field(None, max_length=20)
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    heat_number: Optional[str] = Field(None, max_length=100)
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    certificate_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class MaterialInstanceUpdate(BaseModel):
    """Schema for updating a material instance."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    revision: Optional[str] = Field(None, max_length=20)
    unit_cost: Optional[float] = Field(None, ge=0)
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    heat_number: Optional[str] = Field(None, max_length=100)
    condition: Optional[MaterialCondition] = None
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    certificate_number: Optional[str] = Field(None, max_length=100)
    certificate_received: Optional[bool] = None
    inspection_passed: Optional[bool] = None
    inspection_notes: Optional[str] = None
    project_reference: Optional[str] = Field(None, max_length=100)
    work_order_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class MaterialStatusChangeRequest(BaseModel):
    """Schema for changing material instance status."""
    new_status: MaterialLifecycleStatus
    reason: Optional[str] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    # Optional fields for specific status changes
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    inspection_passed: Optional[bool] = None
    inspection_notes: Optional[str] = None


class MaterialInstanceResponse(BaseModel):
    """Schema for material instance response."""
    id: int
    item_number: str
    title: str
    material_id: int
    purchase_order_id: Optional[int]
    po_line_item_id: Optional[int]
    grn_line_item_id: Optional[int]
    supplier_id: Optional[int]
    specification: Optional[str]
    revision: Optional[str]
    quantity: float
    reserved_quantity: float
    issued_quantity: float
    available_quantity: float
    unit_of_measure: str
    unit_cost: Optional[float]
    lot_number: Optional[str]
    batch_number: Optional[str]
    serial_number: Optional[str]
    heat_number: Optional[str]
    lifecycle_status: MaterialLifecycleStatus
    condition: MaterialCondition
    order_date: Optional[date]
    received_date: Optional[date]
    inspection_date: Optional[date]
    manufacture_date: Optional[date]
    expiry_date: Optional[date]
    storage_location: Optional[str]
    bin_number: Optional[str]
    certificate_number: Optional[str]
    certificate_received: bool
    inspection_passed: Optional[bool]
    inspection_notes: Optional[str]
    po_reference: Optional[str]
    project_reference: Optional[str]
    work_order_reference: Optional[str]
    is_available: bool
    is_expired: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MaterialInstanceDetailResponse(MaterialInstanceResponse):
    """Detailed material instance response with related data."""
    material_name: Optional[str] = None
    material_part_number: Optional[str] = None
    supplier_name: Optional[str] = None
    po_number: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Material Allocation Schemas
# =============================================================================

class MaterialAllocationBase(BaseModel):
    """Base schema for material allocation."""
    material_instance_id: int
    quantity_allocated: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    required_date: Optional[date] = None
    priority: int = Field(default=5, ge=1, le=10)
    notes: Optional[str] = None


class MaterialAllocationCreate(MaterialAllocationBase):
    """Schema for creating material allocation."""
    project_id: Optional[int] = None
    bom_id: Optional[int] = None
    work_order_reference: Optional[str] = Field(None, max_length=100)
    
    @field_validator('project_id', 'bom_id', 'work_order_reference')
    @classmethod
    def at_least_one_target(cls, v, info):
        return v


class MaterialAllocationUpdate(BaseModel):
    """Schema for updating material allocation."""
    quantity_allocated: Optional[float] = Field(None, gt=0)
    required_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class MaterialIssueRequest(BaseModel):
    """Schema for issuing allocated material."""
    quantity_to_issue: float = Field(..., gt=0)
    notes: Optional[str] = None


class MaterialReturnRequest(BaseModel):
    """Schema for returning issued material."""
    quantity_to_return: float = Field(..., gt=0)
    reason: str
    notes: Optional[str] = None


class MaterialAllocationResponse(BaseModel):
    """Schema for material allocation response."""
    id: int
    allocation_number: str
    material_instance_id: int
    project_id: Optional[int]
    bom_id: Optional[int]
    work_order_reference: Optional[str]
    quantity_allocated: float
    quantity_issued: float
    quantity_returned: float
    outstanding_quantity: float
    unit_of_measure: str
    is_active: bool
    is_fulfilled: bool
    allocation_date: date
    required_date: Optional[date]
    issued_date: Optional[date]
    priority: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Material Status History Schemas
# =============================================================================

class MaterialStatusHistoryResponse(BaseModel):
    """Schema for material status history response."""
    id: int
    material_instance_id: int
    from_status: Optional[MaterialLifecycleStatus]
    to_status: MaterialLifecycleStatus
    changed_by_id: int
    changed_by_name: Optional[str] = None
    reference_type: Optional[str]
    reference_number: Optional[str]
    reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# BOM Source Tracking Schemas
# =============================================================================

class BOMSourceTrackingBase(BaseModel):
    """Base schema for BOM source tracking."""
    bom_id: int
    bom_item_id: int
    quantity_required: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    required_date: Optional[date] = None
    notes: Optional[str] = None


class BOMSourceTrackingCreate(BOMSourceTrackingBase):
    """Schema for creating BOM source tracking."""
    purchase_order_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    material_instance_id: Optional[int] = None


class BOMSourceTrackingUpdate(BaseModel):
    """Schema for updating BOM source tracking."""
    purchase_order_id: Optional[int] = None
    po_line_item_id: Optional[int] = None
    material_instance_id: Optional[int] = None
    quantity_allocated: Optional[float] = Field(None, ge=0)
    quantity_consumed: Optional[float] = Field(None, ge=0)
    is_fulfilled: Optional[bool] = None
    notes: Optional[str] = None


class BOMSourceTrackingResponse(BaseModel):
    """Schema for BOM source tracking response."""
    id: int
    bom_id: int
    bom_item_id: int
    purchase_order_id: Optional[int]
    po_line_item_id: Optional[int]
    material_instance_id: Optional[int]
    quantity_required: float
    quantity_allocated: float
    quantity_consumed: float
    shortage_quantity: float
    unit_of_measure: str
    is_fulfilled: bool
    required_date: Optional[date]
    allocated_date: Optional[date]
    consumed_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Material Receipt from PO Schemas
# =============================================================================

class MaterialReceiptFromPORequest(BaseModel):
    """Schema for receiving materials from a PO line item."""
    po_line_item_id: int
    quantity_received: float = Field(..., gt=0)
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    heat_number: Optional[str] = Field(None, max_length=100)
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: str = Field(..., max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    certificate_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class BulkMaterialReceiptRequest(BaseModel):
    """Schema for bulk material receipt from PO."""
    grn_id: int
    items: List[MaterialReceiptFromPORequest]


# =============================================================================
# Material Inspection Schemas
# =============================================================================

class MaterialInspectionRequest(BaseModel):
    """Schema for material inspection."""
    inspection_passed: bool
    inspection_notes: Optional[str] = None
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    rejection_reason: Optional[str] = None


# =============================================================================
# Project Material Summary Schemas
# =============================================================================

class ProjectMaterialSummary(BaseModel):
    """Schema for project material requirements summary."""
    project_id: int
    project_name: str
    total_materials_required: int
    total_materials_allocated: int
    total_materials_issued: int
    materials_pending: int
    allocation_percentage: float
    materials: List[MaterialAllocationResponse]


class BOMSourceSummary(BaseModel):
    """Schema for BOM sourcing summary."""
    bom_id: int
    bom_name: str
    total_items: int
    items_with_po: int
    items_allocated: int
    items_consumed: int
    sourcing_percentage: float
    shortage_items: int
    sources: List[BOMSourceTrackingResponse]


# =============================================================================
# Material Lifecycle Report Schemas
# =============================================================================

class MaterialLifecycleReport(BaseModel):
    """Schema for material lifecycle report."""
    material_instance_id: int
    item_number: str
    title: str
    current_status: MaterialLifecycleStatus
    po_number: Optional[str]
    supplier_name: Optional[str]
    order_date: Optional[date]
    received_date: Optional[date]
    days_in_current_status: int
    status_history: List[MaterialStatusHistoryResponse]


class MaterialInventorySummary(BaseModel):
    """Schema for material inventory summary by status."""
    status: MaterialLifecycleStatus
    count: int
    total_quantity: float
    total_value: float
