"""Workflow and approval models for business process management."""
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean, DateTime, Integer, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class WorkflowType(str, enum.Enum):
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


class WorkflowStatus(str, enum.Enum):
    """Status of a workflow instance."""
    DRAFT = "draft"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class ApprovalStatus(str, enum.Enum):
    """Status of an approval step."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    DELEGATED = "delegated"


class WorkflowTemplate(Base, TimestampMixin):
    """Template defining workflow steps and approval hierarchy."""
    
    __tablename__ = "workflow_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    workflow_type: Mapped[WorkflowType] = mapped_column(Enum(WorkflowType), nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Threshold for auto-approval (if amount below this, auto-approve)
    auto_approve_threshold: Mapped[Optional[float]] = mapped_column(Numeric(14, 4), nullable=True)
    
    # SLA in hours
    sla_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    steps: Mapped[List["WorkflowStep"]] = relationship(
        "WorkflowStep", 
        back_populates="template",
        order_by="WorkflowStep.step_order"
    )
    instances: Mapped[List["WorkflowInstance"]] = relationship("WorkflowInstance", back_populates="template")
    
    def __repr__(self) -> str:
        return f"<WorkflowTemplate(id={self.id}, code='{self.code}', type='{self.workflow_type}')>"


class WorkflowStep(Base, TimestampMixin):
    """Individual step in a workflow template."""
    
    __tablename__ = "workflow_steps"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"), nullable=False)
    
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Approver configuration - can be role-based or specific user
    approver_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # UserRole value
    approver_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # If amount exceeds this, require this step
    amount_threshold: Mapped[Optional[float]] = mapped_column(Numeric(14, 4), nullable=True)
    
    # Escalation
    escalation_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    escalate_to_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_delegation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    template: Mapped["WorkflowTemplate"] = relationship("WorkflowTemplate", back_populates="steps")
    approver_user = relationship("User", foreign_keys=[approver_user_id])
    escalate_to_user = relationship("User", foreign_keys=[escalate_to_user_id])
    
    def __repr__(self) -> str:
        return f"<WorkflowStep(id={self.id}, template_id={self.template_id}, order={self.step_order})>"


class WorkflowInstance(Base, TimestampMixin):
    """Active instance of a workflow."""
    
    __tablename__ = "workflow_instances"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"), nullable=False)
    
    # Reference to the entity being approved
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'order', 'requisition', etc.
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Workflow state
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.DRAFT,
        nullable=False
    )
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Amount for threshold-based approvals
    amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Requestor
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Timing
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Priority
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)  # low, normal, high, urgent
    
    # Additional data as JSON
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    template: Mapped["WorkflowTemplate"] = relationship("WorkflowTemplate", back_populates="instances")
    requestor = relationship("User", foreign_keys=[requested_by])
    approvals: Mapped[List["WorkflowApproval"]] = relationship(
        "WorkflowApproval", 
        back_populates="workflow_instance",
        order_by="WorkflowApproval.step_number"
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowInstance(id={self.id}, ref='{self.reference_number}', status='{self.status}')>"


class WorkflowApproval(Base, TimestampMixin):
    """Individual approval record for a workflow step."""
    
    __tablename__ = "workflow_approvals"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_instance_id: Mapped[int] = mapped_column(ForeignKey("workflow_instances.id"), nullable=False)
    workflow_step_id: Mapped[int] = mapped_column(ForeignKey("workflow_steps.id"), nullable=False)
    
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Approver
    approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    delegated_from_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Approval details
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False
    )
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Comments
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Escalation tracking
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    original_approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Digital signature
    signature_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship("WorkflowInstance", back_populates="approvals")
    workflow_step = relationship("WorkflowStep")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approver_id], back_populates="workflow_approvals")
    delegated_from = relationship("User", foreign_keys=[delegated_from_id])
    original_approver = relationship("User", foreign_keys=[original_approver_id])
    
    def __repr__(self) -> str:
        return f"<WorkflowApproval(id={self.id}, instance_id={self.workflow_instance_id}, status='{self.status}')>"
