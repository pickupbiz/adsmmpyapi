"""Workflow Pydantic schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class WorkflowType(str, Enum):
    """Type of workflow."""
    PURCHASE_ORDER = "purchase_order"
    MATERIAL_REQUISITION = "material_requisition"
    MATERIAL_RECEIPT = "material_receipt"
    MATERIAL_ISSUE = "material_issue"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"
    QUALITY_INSPECTION = "quality_inspection"
    MATERIAL_RETURN = "material_return"
    SCRAP_REQUEST = "scrap_request"
    PROJECT_APPROVAL = "project_approval"
    BOM_CHANGE = "bom_change"


class WorkflowStatus(str, Enum):
    """Status of a workflow instance."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class ApprovalStatus(str, Enum):
    """Status of an approval step."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    DELEGATED = "delegated"


# Workflow Template Schemas
class WorkflowTemplateBase(BaseModel):
    """Base workflow template schema."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    workflow_type: WorkflowType
    description: Optional[str] = None
    is_active: bool = True
    auto_approve_threshold: Optional[float] = Field(None, ge=0)
    sla_hours: Optional[int] = Field(None, ge=0)


class WorkflowTemplateCreate(WorkflowTemplateBase):
    """Schema for creating a workflow template."""
    pass


class WorkflowTemplateUpdate(BaseModel):
    """Schema for updating a workflow template."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    auto_approve_threshold: Optional[float] = Field(None, ge=0)
    sla_hours: Optional[int] = Field(None, ge=0)


class WorkflowTemplateResponse(WorkflowTemplateBase):
    """Schema for workflow template response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Workflow Step Schemas
class WorkflowStepBase(BaseModel):
    """Base workflow step schema."""
    template_id: int
    step_order: int
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    approver_role: Optional[str] = Field(None, max_length=50)
    approver_user_id: Optional[int] = None
    amount_threshold: Optional[float] = Field(None, ge=0)
    escalation_hours: Optional[int] = Field(None, ge=0)
    escalate_to_user_id: Optional[int] = None
    is_mandatory: bool = True
    allow_delegation: bool = False


class WorkflowStepCreate(WorkflowStepBase):
    """Schema for creating a workflow step."""
    pass


class WorkflowStepUpdate(BaseModel):
    """Schema for updating a workflow step."""
    step_order: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    approver_role: Optional[str] = Field(None, max_length=50)
    approver_user_id: Optional[int] = None
    amount_threshold: Optional[float] = Field(None, ge=0)
    escalation_hours: Optional[int] = Field(None, ge=0)
    escalate_to_user_id: Optional[int] = None
    is_mandatory: Optional[bool] = None
    allow_delegation: Optional[bool] = None


class WorkflowStepResponse(WorkflowStepBase):
    """Schema for workflow step response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Workflow Instance Schemas
class WorkflowInstanceBase(BaseModel):
    """Base workflow instance schema."""
    template_id: int
    reference_type: str = Field(..., max_length=50)
    reference_id: int
    reference_number: str = Field(..., max_length=100)
    amount: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    due_date: Optional[datetime] = None
    priority: str = Field("normal", max_length=20)
    extra_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class WorkflowInstanceCreate(WorkflowInstanceBase):
    """Schema for creating a workflow instance."""
    pass


class WorkflowInstanceUpdate(BaseModel):
    """Schema for updating a workflow instance."""
    status: Optional[WorkflowStatus] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, max_length=20)
    extra_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class WorkflowInstanceResponse(WorkflowInstanceBase):
    """Schema for workflow instance response."""
    id: int
    status: WorkflowStatus
    current_step: int
    requested_by: int
    requested_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Workflow Approval Schemas
class WorkflowApprovalAction(BaseModel):
    """Schema for approving/rejecting a workflow."""
    action: ApprovalStatus  # approved or rejected
    comments: Optional[str] = None


class WorkflowApprovalResponse(BaseModel):
    """Schema for workflow approval response."""
    id: int
    workflow_instance_id: int
    workflow_step_id: int
    step_number: int
    approver_id: Optional[int]
    status: ApprovalStatus
    decision_at: Optional[datetime]
    comments: Optional[str]
    is_escalated: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Enhanced Workflow Schemas for PO Integration
# =============================================================================

class POSubmitRequest(BaseModel):
    """Schema for submitting PO for approval."""
    notes: Optional[str] = None


class POApprovalStatusResponse(BaseModel):
    """Schema for PO approval status response."""
    po_number: str
    po_status: str
    total_amount: float
    currency: str
    workflow: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = []


class MaterialIssueSubmitRequest(BaseModel):
    """Schema for submitting material issue for approval."""
    notes: Optional[str] = None


class QualityInspectionApproval(BaseModel):
    """Schema for QA inspection approval."""
    passed: bool
    inspection_notes: str


class PendingApprovalItem(BaseModel):
    """Schema for a pending approval item."""
    approval_id: int
    instance_id: int
    reference_type: str
    reference_number: str
    amount: float
    currency: str
    requested_at: datetime
    priority: str


class PendingPOItem(BaseModel):
    """Schema for a pending PO item."""
    id: int
    po_number: str
    total_amount: float
    currency: str
    created_at: datetime


class PendingInspectionItem(BaseModel):
    """Schema for a pending inspection item."""
    id: int
    item_number: str
    material_id: int
    quantity: float
    received_date: Optional[datetime] = None


class MyApprovalsResponse(BaseModel):
    """Schema for my approvals dashboard."""
    workflow_approvals: List[PendingApprovalItem] = []
    pending_pos: List[PendingPOItem] = []
    pending_inspections: List[PendingInspectionItem] = []
    total_pending: int


class AuditLogEntry(BaseModel):
    """Schema for audit log entry."""
    id: int
    action: str
    user: Optional[str] = None
    description: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    timestamp: datetime
    ip_address: Optional[str] = None


class ApprovalThresholds(BaseModel):
    """Schema for approval thresholds configuration."""
    low: float = 5000.0
    standard: float = 25000.0
    high: float = 100000.0
    
    
class WorkflowInstanceDetailResponse(WorkflowInstanceResponse):
    """Detailed workflow instance response with approvals."""
    template_name: Optional[str] = None
    requestor_name: Optional[str] = None
    approvals: List[WorkflowApprovalResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
