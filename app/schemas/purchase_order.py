"""Pydantic schemas for Purchase Order management."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ============== Enums ==============

class POStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class POPriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    AOG = "aog"


class MaterialStageEnum(str, Enum):
    ON_ORDER = "on_order"
    RAW_MATERIAL = "raw_material"
    IN_INSPECTION = "in_inspection"
    WIP = "wip"
    FINISHED_GOODS = "finished_goods"
    CONSUMED = "consumed"
    SCRAPPED = "scrapped"


class GRNStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_INSPECTION = "pending_inspection"
    INSPECTION_PASSED = "inspection_passed"
    INSPECTION_FAILED = "inspection_failed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"


class ApprovalActionEnum(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    CANCELLED = "cancelled"


# ============== PO Line Item Schemas ==============

class POLineItemBase(BaseModel):
    """Base schema for PO line items."""
    material_id: int
    quantity_ordered: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = Field(default=0, ge=0, le=100)
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    specification: Optional[str] = Field(None, max_length=200)
    revision: Optional[str] = Field(None, max_length=20)
    requires_certification: bool = False
    requires_inspection: bool = True
    notes: Optional[str] = None


class POLineItemCreate(POLineItemBase):
    """Schema for creating PO line items."""
    pass


class POLineItemUpdate(BaseModel):
    """Schema for updating PO line items."""
    quantity_ordered: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, ge=0)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    specification: Optional[str] = None
    revision: Optional[str] = None
    requires_certification: Optional[bool] = None
    requires_inspection: Optional[bool] = None
    notes: Optional[str] = None


class POLineItemResponse(POLineItemBase):
    """Schema for PO line item responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    purchase_order_id: int
    line_number: int
    quantity_received: float = 0
    quantity_accepted: float = 0
    quantity_rejected: float = 0
    total_price: float
    material_stage: MaterialStageEnum
    certification_received: bool = False
    inspection_completed: bool = False
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_fully_received: bool = False
    outstanding_quantity: float = 0


# ============== Purchase Order Schemas ==============

class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Orders."""
    supplier_id: int
    priority: POPriorityEnum = POPriorityEnum.NORMAL
    required_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    
    # Financial
    tax_amount: float = Field(default=0, ge=0)
    shipping_cost: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=3)
    
    # Shipping
    shipping_method: Optional[str] = Field(None, max_length=100)
    shipping_address: Optional[str] = None
    
    # References
    requisition_number: Optional[str] = Field(None, max_length=100)
    project_reference: Optional[str] = Field(None, max_length=100)
    work_order_reference: Optional[str] = Field(None, max_length=100)
    
    # Compliance
    requires_certification: bool = True
    requires_inspection: bool = True
    
    # Terms
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_terms: Optional[str] = Field(None, max_length=100)
    
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating Purchase Orders."""
    line_items: List[POLineItemCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating Purchase Orders."""
    supplier_id: Optional[int] = None
    priority: Optional[POPriorityEnum] = None
    required_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    tax_amount: Optional[float] = Field(None, ge=0)
    shipping_cost: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    shipping_method: Optional[str] = None
    shipping_address: Optional[str] = None
    requisition_number: Optional[str] = None
    project_reference: Optional[str] = None
    work_order_reference: Optional[str] = None
    requires_certification: Optional[bool] = None
    requires_inspection: Optional[bool] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    po_number: str
    created_by_id: int
    approved_by_id: Optional[int] = None
    status: POStatusEnum
    po_date: date
    approved_date: Optional[datetime] = None
    ordered_date: Optional[date] = None
    subtotal: float
    total_amount: float
    requires_approval: bool
    approval_threshold: Optional[float] = None
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    tracking_number: Optional[str] = None
    revision_number: int
    created_at: datetime
    updated_at: datetime
    
    line_items: List[POLineItemResponse] = []


class PurchaseOrderListResponse(BaseModel):
    """Schema for PO list responses with pagination."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    po_number: str
    supplier_id: int
    status: POStatusEnum
    priority: POPriorityEnum
    po_date: date
    total_amount: float
    currency: str
    required_date: Optional[date] = None
    created_at: datetime


# ============== PO Approval Schemas ==============

class POApprovalRequest(BaseModel):
    """Schema for PO approval/rejection request."""
    action: ApprovalActionEnum
    comments: Optional[str] = None


class POApprovalHistoryResponse(BaseModel):
    """Schema for PO approval history responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    purchase_order_id: int
    user_id: int
    action: ApprovalActionEnum
    from_status: Optional[POStatusEnum] = None
    to_status: POStatusEnum
    comments: Optional[str] = None
    po_total_at_action: Optional[float] = None
    po_revision_at_action: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: datetime


# ============== GRN Line Item Schemas ==============

class GRNLineItemBase(BaseModel):
    """Base schema for GRN line items."""
    po_line_item_id: int
    quantity_received: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., max_length=20)
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    serial_numbers: Optional[str] = None
    heat_number: Optional[str] = Field(None, max_length=100)
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_location: Optional[str] = Field(None, max_length=100)
    bin_number: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class GRNLineItemCreate(GRNLineItemBase):
    """Schema for creating GRN line items."""
    pass


class GRNLineItemUpdate(BaseModel):
    """Schema for updating GRN line items."""
    quantity_accepted: Optional[float] = Field(None, ge=0)
    quantity_rejected: Optional[float] = Field(None, ge=0)
    inspection_status: Optional[str] = None
    inspection_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    ncr_number: Optional[str] = None
    storage_location: Optional[str] = None
    bin_number: Optional[str] = None
    notes: Optional[str] = None


class GRNLineItemResponse(GRNLineItemBase):
    """Schema for GRN line item responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    goods_receipt_id: int
    quantity_accepted: float = 0
    quantity_rejected: float = 0
    inspection_status: Optional[str] = None
    inspection_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    ncr_number: Optional[str] = None
    inventory_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ============== Goods Receipt Note Schemas ==============

class GoodsReceiptNoteBase(BaseModel):
    """Base schema for Goods Receipt Notes."""
    purchase_order_id: int
    receipt_date: date = Field(default_factory=date.today)
    delivery_note_number: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=100)
    carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    packing_slip_received: bool = False
    coc_received: bool = False
    mtr_received: bool = False
    storage_location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class GoodsReceiptNoteCreate(GoodsReceiptNoteBase):
    """Schema for creating Goods Receipt Notes."""
    line_items: List[GRNLineItemCreate] = Field(default_factory=list)


class GoodsReceiptNoteUpdate(BaseModel):
    """Schema for updating Goods Receipt Notes."""
    delivery_note_number: Optional[str] = None
    invoice_number: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    packing_slip_received: Optional[bool] = None
    coc_received: Optional[bool] = None
    mtr_received: Optional[bool] = None
    storage_location: Optional[str] = None
    notes: Optional[str] = None
    inspection_notes: Optional[str] = None


class GoodsReceiptNoteResponse(GoodsReceiptNoteBase):
    """Schema for Goods Receipt Note responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    grn_number: str
    received_by_id: int
    inspected_by_id: Optional[int] = None
    status: GRNStatusEnum
    inspection_date: Optional[date] = None
    inspection_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    line_items: List[GRNLineItemResponse] = []


# ============== Material Lifecycle Schemas ==============

class MaterialLifecycleUpdate(BaseModel):
    """Schema for updating material lifecycle stage."""
    material_stage: MaterialStageEnum
    notes: Optional[str] = None


class MaterialLifecycleTracker(BaseModel):
    """Schema for tracking material through lifecycle."""
    model_config = ConfigDict(from_attributes=True)
    
    po_line_item_id: int
    material_id: int
    material_name: str
    part_number: str
    current_stage: MaterialStageEnum
    quantity_ordered: float
    quantity_received: float
    quantity_accepted: float
    quantity_in_wip: float = 0
    quantity_finished: float = 0
    quantity_consumed: float = 0


# ============== Summary/Dashboard Schemas ==============

class POSummary(BaseModel):
    """Schema for PO summary statistics."""
    total_pos: int = 0
    draft_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    ordered_count: int = 0
    received_count: int = 0
    total_value: float = 0
    pending_value: float = 0


class SupplierPOSummary(BaseModel):
    """Schema for supplier PO summary."""
    supplier_id: int
    supplier_name: str
    total_pos: int = 0
    open_pos: int = 0
    total_value: float = 0
    open_value: float = 0
    on_time_delivery_rate: Optional[float] = None
