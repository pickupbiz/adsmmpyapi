"""
Workflow management endpoints with PO and material movement approval.

Provides:
- PO approval workflow management
- Material issuance/consumption approval
- Two-level approval system
- Role-based approval endpoints
- Audit trail logging
- Email notifications
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from decimal import Decimal

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.workflow import (
    WorkflowTemplate, WorkflowStep, WorkflowInstance, WorkflowApproval,
    WorkflowType, WorkflowStatus, ApprovalStatus
)
from app.models.purchase_order import PurchaseOrder, POStatus, POApprovalHistory, ApprovalAction
from app.models.material_instance import MaterialInstance, MaterialAllocation, MaterialStatusHistory, MaterialLifecycleStatus
from app.models.audit import AuditLog, AuditAction
from app.schemas.workflow import (
    WorkflowTemplateCreate, WorkflowTemplateUpdate, WorkflowTemplateResponse,
    WorkflowStepCreate, WorkflowStepUpdate, WorkflowStepResponse,
    WorkflowInstanceCreate, WorkflowInstanceUpdate, WorkflowInstanceResponse,
    WorkflowApprovalAction, WorkflowApprovalResponse,
    WorkflowType as SchemaWorkflowType, WorkflowStatus as SchemaWorkflowStatus,
    ApprovalStatus as SchemaApprovalStatus
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    get_current_user, require_director, require_head_of_operations,
    require_purchase, require_store, require_qa, require_any_role,
    PaginationParams
)
from app.core.notifications import notification_service


router = APIRouter(prefix="/workflows", tags=["Workflows"])


# =============================================================================
# Approval Thresholds Configuration
# =============================================================================

# Amount thresholds for different approval levels (in base currency)
APPROVAL_THRESHOLDS = {
    "low": 5000.0,           # Auto-approve if under this (optional)
    "standard": 25000.0,      # Head of Operations can approve
    "high": 100000.0,         # Director approval required
    "critical": float('inf')  # Multiple approvals required
}

# Role-based approval permissions
ROLE_APPROVAL_LIMITS = {
    UserRole.DIRECTOR: float('inf'),      # Can approve any amount
    UserRole.HEAD_OF_OPERATIONS: 100000.0, # Up to 100K
    UserRole.PURCHASE: 25000.0,            # Up to 25K (for supplier/material approvals)
    UserRole.STORE: 10000.0,               # Up to 10K (material movements)
    UserRole.QA: 50000.0,                  # Quality-related approvals
}


# =============================================================================
# Helper Functions
# =============================================================================

def can_user_approve(user: User, amount: float, workflow_type: WorkflowType) -> bool:
    """Check if user can approve based on role and amount."""
    if user.role == UserRole.DIRECTOR or user.role == UserRole.ADMIN:
        return True
    
    user_limit = ROLE_APPROVAL_LIMITS.get(user.role, 0)
    
    # Check user's personal approval limit if set
    if user.approval_limit and user.approval_limit > 0:
        user_limit = min(user_limit, float(user.approval_limit))
    
    return amount <= user_limit


def get_required_approvers(amount: float, workflow_type: WorkflowType) -> List[str]:
    """Get list of required approver roles based on amount and type."""
    approvers = []
    
    if workflow_type == WorkflowType.PURCHASE_ORDER:
        if amount <= APPROVAL_THRESHOLDS["standard"]:
            approvers = [UserRole.HEAD_OF_OPERATIONS.value]
        elif amount <= APPROVAL_THRESHOLDS["high"]:
            approvers = [UserRole.HEAD_OF_OPERATIONS.value, UserRole.DIRECTOR.value]
        else:
            approvers = [UserRole.HEAD_OF_OPERATIONS.value, UserRole.DIRECTOR.value]
    
    elif workflow_type == WorkflowType.MATERIAL_ISSUE:
        if amount <= APPROVAL_THRESHOLDS["low"]:
            approvers = [UserRole.STORE.value]
        else:
            approvers = [UserRole.STORE.value, UserRole.HEAD_OF_OPERATIONS.value]
    
    elif workflow_type == WorkflowType.QUALITY_INSPECTION:
        approvers = [UserRole.QA.value]
    
    elif workflow_type == WorkflowType.MATERIAL_RECEIPT:
        approvers = [UserRole.STORE.value, UserRole.QA.value]
    
    return approvers


def log_audit(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_id: int,
    description: str,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    request: Optional[Request] = None
):
    """Log an audit trail entry."""
    audit_log = AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:255] if request else None
    )
    db.add(audit_log)


def notify_approvers(
    db: Session,
    workflow: WorkflowInstance,
    approver_role: str
):
    """Send notifications to users with the approver role."""
    users = db.query(User).filter(
        User.role == approver_role,
        User.is_active == True,
        User.can_approve_workflows == True
    ).all()
    
    # Get PO details if this is a PO workflow
    if workflow.reference_type == "purchase_order":
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == workflow.reference_id).first()
        if po:
            requestor = db.query(User).filter(User.id == workflow.requested_by).first()
            for user in users:
                if user.email:
                    notification_service.notify_po_pending_approval(
                        approver_email=user.email,
                        approver_name=user.full_name or user.username,
                        po_number=po.po_number,
                        total_amount=float(po.total_amount or 0),
                        currency=po.currency,
                        supplier_name=po.supplier.name if po.supplier else "Unknown",
                        requestor_name=requestor.full_name if requestor else "Unknown"
                    )


# =============================================================================
# Workflow Template Endpoints
# =============================================================================

@router.get("/templates", response_model=List[WorkflowTemplateResponse])
def list_workflow_templates(
    workflow_type: Optional[SchemaWorkflowType] = Query(None),
    is_active: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List workflow templates."""
    query = db.query(WorkflowTemplate)
    
    if workflow_type:
        query = query.filter(WorkflowTemplate.workflow_type == workflow_type.value)
    if is_active is not None:
        query = query.filter(WorkflowTemplate.is_active == is_active)
    
    return query.all()


@router.post("/templates", response_model=WorkflowTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_template(
    template_in: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_director)
):
    """Create a new workflow template (Director only)."""
    # Check if code already exists
    existing = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.code == template_in.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with code '{template_in.code}' already exists"
        )
    
    template = WorkflowTemplate(**template_in.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
def get_workflow_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get workflow template details."""
    template = db.query(WorkflowTemplate).options(
        joinedload(WorkflowTemplate.steps)
    ).filter(WorkflowTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    return template


@router.put("/templates/{template_id}", response_model=WorkflowTemplateResponse)
def update_workflow_template(
    template_id: int,
    template_in: WorkflowTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_director)
):
    """Update workflow template (Director only)."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template


# =============================================================================
# Workflow Step Endpoints
# =============================================================================

@router.post("/templates/{template_id}/steps", response_model=WorkflowStepResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_step(
    template_id: int,
    step_in: WorkflowStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_director)
):
    """Add a step to a workflow template (Director only)."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    step_data = step_in.model_dump()
    step_data['template_id'] = template_id
    step = WorkflowStep(**step_data)
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@router.get("/templates/{template_id}/steps", response_model=List[WorkflowStepResponse])
def list_workflow_steps(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List steps for a workflow template."""
    steps = db.query(WorkflowStep).filter(
        WorkflowStep.template_id == template_id
    ).order_by(WorkflowStep.step_order).all()
    return steps


# =============================================================================
# Workflow Instance Endpoints
# =============================================================================

@router.get("/instances", response_model=PaginatedResponse[WorkflowInstanceResponse])
def list_workflow_instances(
    pagination: PaginationParams = Depends(),
    workflow_type: Optional[SchemaWorkflowType] = Query(None),
    status_filter: Optional[SchemaWorkflowStatus] = Query(None, alias="status"),
    my_approvals: bool = Query(False, description="Only show workflows pending my approval"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List workflow instances with filtering."""
    query = db.query(WorkflowInstance)
    
    if workflow_type:
        query = query.join(WorkflowTemplate).filter(
            WorkflowTemplate.workflow_type == workflow_type.value
        )
    
    if status_filter:
        query = query.filter(WorkflowInstance.status == status_filter.value)
    
    if my_approvals:
        # Find instances where current step matches user's role
        query = query.join(
            WorkflowApproval,
            and_(
                WorkflowApproval.workflow_instance_id == WorkflowInstance.id,
                WorkflowApproval.step_number == WorkflowInstance.current_step,
                WorkflowApproval.status == ApprovalStatus.PENDING
            )
        ).join(
            WorkflowStep,
            WorkflowApproval.workflow_step_id == WorkflowStep.id
        ).filter(
            or_(
                WorkflowStep.approver_role == current_user.role.value,
                WorkflowStep.approver_user_id == current_user.id
            )
        )
    
    total = query.count()
    instances = query.order_by(WorkflowInstance.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=instances,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.post("/instances", response_model=WorkflowInstanceResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_instance(
    instance_in: WorkflowInstanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Create a new workflow instance (submit for approval)."""
    # Get template
    template = db.query(WorkflowTemplate).options(
        joinedload(WorkflowTemplate.steps)
    ).filter(WorkflowTemplate.id == instance_in.template_id).first()
    
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow template not found")
    
    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow template is not active"
        )
    
    # Check auto-approve threshold
    auto_approve = False
    if template.auto_approve_threshold and instance_in.amount:
        if instance_in.amount < template.auto_approve_threshold:
            auto_approve = True
    
    # Create instance
    instance = WorkflowInstance(
        template_id=template.id,
        reference_type=instance_in.reference_type,
        reference_id=instance_in.reference_id,
        reference_number=instance_in.reference_number,
        amount=instance_in.amount,
        currency=instance_in.currency,
        requested_by=current_user.id,
        due_date=instance_in.due_date or (datetime.utcnow() + timedelta(hours=template.sla_hours or 72)),
        priority=instance_in.priority,
        extra_data=instance_in.extra_data,
        notes=instance_in.notes,
        status=WorkflowStatus.APPROVED if auto_approve else WorkflowStatus.PENDING,
        current_step=1
    )
    db.add(instance)
    db.flush()
    
    # Create approval records for each step
    for step in template.steps:
        approval = WorkflowApproval(
            workflow_instance_id=instance.id,
            workflow_step_id=step.id,
            step_number=step.step_order,
            status=ApprovalStatus.APPROVED if auto_approve else ApprovalStatus.PENDING
        )
        if auto_approve:
            approval.decision_at = datetime.utcnow()
            approval.comments = "Auto-approved (below threshold)"
        db.add(approval)
    
    if auto_approve:
        instance.completed_at = datetime.utcnow()
    
    # Log audit
    log_audit(
        db, current_user, AuditAction.CREATE.value, "workflow_instance", instance.id,
        f"Created workflow instance for {instance_in.reference_type} {instance_in.reference_number}",
        new_values={"amount": float(instance_in.amount or 0), "status": instance.status.value},
        request=request
    )
    
    db.commit()
    db.refresh(instance)
    
    # Notify first approver if not auto-approved
    if not auto_approve and template.steps:
        first_step = template.steps[0]
        if first_step.approver_role:
            notify_approvers(db, instance, first_step.approver_role)
    
    return instance


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
def get_workflow_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get workflow instance details."""
    instance = db.query(WorkflowInstance).options(
        joinedload(WorkflowInstance.template),
        joinedload(WorkflowInstance.approvals).joinedload(WorkflowApproval.approver)
    ).filter(WorkflowInstance.id == instance_id).first()
    
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow instance not found")
    
    return instance


# =============================================================================
# Approval Action Endpoints
# =============================================================================

@router.post("/instances/{instance_id}/approve", response_model=WorkflowApprovalResponse)
def approve_workflow(
    instance_id: int,
    approval_action: WorkflowApprovalAction,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Approve or reject a workflow step."""
    instance = db.query(WorkflowInstance).options(
        joinedload(WorkflowInstance.template).joinedload(WorkflowTemplate.steps),
        joinedload(WorkflowInstance.approvals)
    ).filter(WorkflowInstance.id == instance_id).first()
    
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow instance not found")
    
    if instance.status not in [WorkflowStatus.PENDING, WorkflowStatus.IN_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow is not pending approval (status: {instance.status.value})"
        )
    
    # Find current pending approval
    current_approval = None
    for approval in instance.approvals:
        if approval.step_number == instance.current_step and approval.status == ApprovalStatus.PENDING:
            current_approval = approval
            break
    
    if not current_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending approval found for current step"
        )
    
    # Check if user can approve
    step = current_approval.workflow_step
    can_approve = False
    
    if step.approver_user_id:
        can_approve = step.approver_user_id == current_user.id
    elif step.approver_role:
        can_approve = current_user.role.value == step.approver_role
    
    # Director can always approve
    if current_user.role in [UserRole.DIRECTOR, UserRole.ADMIN]:
        can_approve = True
    
    # Check amount-based permission
    if can_approve and instance.amount:
        can_approve = can_user_approve(current_user, float(instance.amount), instance.template.workflow_type)
    
    if not can_approve:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to approve this workflow"
        )
    
    # Process approval
    old_status = instance.status.value
    current_approval.approver_id = current_user.id
    current_approval.decision_at = datetime.utcnow()
    current_approval.comments = approval_action.comments
    
    if approval_action.action == ApprovalStatus.APPROVED:
        current_approval.status = ApprovalStatus.APPROVED
        
        # Check if there are more steps
        next_step_number = instance.current_step + 1
        next_approval = None
        for approval in instance.approvals:
            if approval.step_number == next_step_number:
                next_approval = approval
                break
        
        if next_approval:
            instance.current_step = next_step_number
            instance.status = WorkflowStatus.IN_REVIEW
            
            # Notify next approvers
            next_step = None
            for s in instance.template.steps:
                if s.step_order == next_step_number:
                    next_step = s
                    break
            if next_step and next_step.approver_role:
                notify_approvers(db, instance, next_step.approver_role)
        else:
            # Final approval - workflow completed
            instance.status = WorkflowStatus.APPROVED
            instance.completed_at = datetime.utcnow()
            
            # Update the referenced entity (e.g., PO)
            _update_entity_on_approval(db, instance, True, current_user, approval_action.comments, request)
    
    elif approval_action.action == ApprovalStatus.REJECTED:
        current_approval.status = ApprovalStatus.REJECTED
        instance.status = WorkflowStatus.REJECTED
        instance.completed_at = datetime.utcnow()
        
        # Update the referenced entity
        _update_entity_on_approval(db, instance, False, current_user, approval_action.comments, request)
    
    # Log audit
    log_audit(
        db, current_user, "APPROVE" if approval_action.action == ApprovalStatus.APPROVED else "REJECT",
        "workflow_instance", instance.id,
        f"{'Approved' if approval_action.action == ApprovalStatus.APPROVED else 'Rejected'} workflow step {instance.current_step}",
        old_values={"status": old_status},
        new_values={"status": instance.status.value, "comments": approval_action.comments},
        request=request
    )
    
    db.commit()
    db.refresh(current_approval)
    
    return current_approval


def _update_entity_on_approval(
    db: Session,
    instance: WorkflowInstance,
    approved: bool,
    approver: User,
    comments: Optional[str],
    request: Optional[Request]
):
    """Update the referenced entity when workflow is approved/rejected."""
    if instance.reference_type == "purchase_order":
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == instance.reference_id).first()
        if po:
            old_status = po.status.value
            requestor = db.query(User).filter(User.id == po.created_by_id).first()
            
            if approved:
                po.status = POStatus.APPROVED
                po.approved_by_id = approver.id
                po.approved_date = datetime.utcnow()
                po.approval_notes = comments
                
                # Notify requestor
                if requestor and requestor.email:
                    notification_service.notify_po_approved(
                        requestor_email=requestor.email,
                        requestor_name=requestor.full_name or requestor.username,
                        po_number=po.po_number,
                        total_amount=float(po.total_amount or 0),
                        currency=po.currency,
                        approver_name=approver.full_name or approver.username,
                        comments=comments
                    )
            else:
                po.status = POStatus.REJECTED
                po.rejection_reason = comments
                
                # Notify requestor
                if requestor and requestor.email:
                    notification_service.notify_po_rejected(
                        requestor_email=requestor.email,
                        requestor_name=requestor.full_name or requestor.username,
                        po_number=po.po_number,
                        total_amount=float(po.total_amount or 0),
                        currency=po.currency,
                        approver_name=approver.full_name or approver.username,
                        rejection_reason=comments or "No reason provided"
                    )
            
            # Record PO approval history
            history = POApprovalHistory(
                purchase_order_id=po.id,
                user_id=approver.id,
                action=ApprovalAction.APPROVED if approved else ApprovalAction.REJECTED,
                from_status=POStatus(old_status),
                to_status=po.status,
                comments=comments,
                po_total_at_action=po.total_amount,
                po_revision_at_action=po.revision_number,
                ip_address=request.client.host if request and request.client else None
            )
            db.add(history)
    
    elif instance.reference_type == "material_issue":
        # Handle material issue approval
        allocation = db.query(MaterialAllocation).filter(
            MaterialAllocation.id == instance.reference_id
        ).first()
        if allocation and approved:
            allocation.status = "approved"
            allocation.approved_at = datetime.utcnow()
            allocation.approved_by_id = approver.id


@router.post("/instances/{instance_id}/cancel", response_model=WorkflowInstanceResponse)
def cancel_workflow(
    instance_id: int,
    reason: str = Query(..., description="Cancellation reason"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Cancel a workflow instance."""
    instance = db.query(WorkflowInstance).filter(WorkflowInstance.id == instance_id).first()
    
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow instance not found")
    
    # Only requestor or admin can cancel
    if instance.requested_by != current_user.id and current_user.role not in [UserRole.DIRECTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requestor or an admin can cancel this workflow"
        )
    
    if instance.status in [WorkflowStatus.APPROVED, WorkflowStatus.REJECTED, WorkflowStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed workflow"
        )
    
    old_status = instance.status.value
    instance.status = WorkflowStatus.CANCELLED
    instance.completed_at = datetime.utcnow()
    instance.notes = f"Cancelled: {reason}" + (f"\n\nOriginal notes: {instance.notes}" if instance.notes else "")
    
    # Log audit
    log_audit(
        db, current_user, "CANCEL", "workflow_instance", instance.id,
        f"Cancelled workflow: {reason}",
        old_values={"status": old_status},
        new_values={"status": instance.status.value},
        request=request
    )
    
    db.commit()
    db.refresh(instance)
    return instance


# =============================================================================
# PO-Specific Approval Endpoints
# =============================================================================

@router.post("/po/{po_id}/submit", response_model=WorkflowInstanceResponse)
def submit_po_for_approval(
    po_id: int,
    notes: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Submit a PO for approval (Purchase role)."""
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Order not found")
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PO must be in draft status to submit (current: {po.status.value})"
        )
    
    # Check if PO has line items
    if not po.line_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PO must have at least one line item"
        )
    
    # Find or create PO approval template
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.workflow_type == WorkflowType.PURCHASE_ORDER,
        WorkflowTemplate.is_active == True
    ).first()
    
    if not template:
        # Create default PO approval template
        template = WorkflowTemplate(
            name="Purchase Order Approval",
            code="PO_APPROVAL",
            workflow_type=WorkflowType.PURCHASE_ORDER,
            description="Standard PO approval workflow",
            auto_approve_threshold=5000.0,
            sla_hours=48
        )
        db.add(template)
        db.flush()
        
        # Add approval steps
        steps = [
            WorkflowStep(
                template_id=template.id,
                step_order=1,
                name="Operations Approval",
                approver_role=UserRole.HEAD_OF_OPERATIONS.value,
                amount_threshold=0,
                is_mandatory=True
            ),
            WorkflowStep(
                template_id=template.id,
                step_order=2,
                name="Director Approval",
                approver_role=UserRole.DIRECTOR.value,
                amount_threshold=APPROVAL_THRESHOLDS["standard"],
                is_mandatory=False  # Only required for high-value POs
            )
        ]
        for step in steps:
            db.add(step)
        db.flush()
    
    # Create workflow instance
    instance = WorkflowInstance(
        template_id=template.id,
        reference_type="purchase_order",
        reference_id=po.id,
        reference_number=po.po_number,
        amount=po.total_amount,
        currency=po.currency,
        requested_by=current_user.id,
        due_date=datetime.utcnow() + timedelta(hours=template.sla_hours or 48),
        priority="high" if float(po.total_amount or 0) > APPROVAL_THRESHOLDS["standard"] else "normal",
        extra_data={
            "supplier_name": po.supplier.name if po.supplier else None,
            "po_date": po.po_date.isoformat() if po.po_date else None,
            "line_item_count": len(po.line_items) if po.line_items else 0
        },
        notes=notes,
        status=WorkflowStatus.PENDING,
        current_step=1
    )
    db.add(instance)
    db.flush()
    
    # Create approval records
    for step in template.steps:
        # Skip non-mandatory steps if amount is below threshold
        if not step.is_mandatory and step.amount_threshold:
            if float(po.total_amount or 0) < step.amount_threshold:
                continue
        
        approval = WorkflowApproval(
            workflow_instance_id=instance.id,
            workflow_step_id=step.id,
            step_number=step.step_order,
            status=ApprovalStatus.PENDING
        )
        db.add(approval)
    
    # Update PO status
    po.status = POStatus.PENDING_APPROVAL
    
    # Record PO history
    history = POApprovalHistory(
        purchase_order_id=po.id,
        user_id=current_user.id,
        action=ApprovalAction.SUBMITTED,
        from_status=POStatus.DRAFT,
        to_status=POStatus.PENDING_APPROVAL,
        comments=notes,
        po_total_at_action=po.total_amount,
        ip_address=request.client.host if request and request.client else None
    )
    db.add(history)
    
    # Log audit
    log_audit(
        db, current_user, "SUBMIT", "purchase_order", po.id,
        f"Submitted PO {po.po_number} for approval (Amount: {po.currency} {po.total_amount})",
        new_values={"status": po.status.value, "workflow_id": instance.id},
        request=request
    )
    
    db.commit()
    db.refresh(instance)
    
    # Notify first approver
    if template.steps:
        first_step = template.steps[0]
        if first_step.approver_role:
            notify_approvers(db, instance, first_step.approver_role)
    
    return instance


@router.get("/po/{po_id}/approval-status")
def get_po_approval_status(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get approval status for a PO."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Order not found")
    
    # Find workflow instance
    instance = db.query(WorkflowInstance).options(
        joinedload(WorkflowInstance.approvals).joinedload(WorkflowApproval.approver)
    ).filter(
        WorkflowInstance.reference_type == "purchase_order",
        WorkflowInstance.reference_id == po_id
    ).order_by(WorkflowInstance.created_at.desc()).first()
    
    # Get approval history
    history = db.query(POApprovalHistory).options(
        joinedload(POApprovalHistory.user)
    ).filter(
        POApprovalHistory.purchase_order_id == po_id
    ).order_by(POApprovalHistory.created_at.desc()).all()
    
    return {
        "po_number": po.po_number,
        "po_status": po.status.value,
        "total_amount": float(po.total_amount or 0),
        "currency": po.currency,
        "workflow": {
            "id": instance.id if instance else None,
            "status": instance.status.value if instance else None,
            "current_step": instance.current_step if instance else None,
            "approvals": [
                {
                    "step": a.step_number,
                    "status": a.status.value,
                    "approver": a.approver.full_name if a.approver else None,
                    "decision_at": a.decision_at.isoformat() if a.decision_at else None,
                    "comments": a.comments
                }
                for a in (instance.approvals if instance else [])
            ]
        } if instance else None,
        "history": [
            {
                "action": h.action.value,
                "user": h.user.full_name if h.user else None,
                "from_status": h.from_status.value if h.from_status else None,
                "to_status": h.to_status.value,
                "comments": h.comments,
                "timestamp": h.created_at.isoformat()
            }
            for h in history
        ]
    }


# =============================================================================
# Material Movement Approval Endpoints
# =============================================================================

@router.post("/material-issue/{allocation_id}/submit", response_model=WorkflowInstanceResponse)
def submit_material_issue_for_approval(
    allocation_id: int,
    notes: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Submit material issue/allocation for approval (Store role)."""
    allocation = db.query(MaterialAllocation).options(
        joinedload(MaterialAllocation.material_instance)
    ).filter(MaterialAllocation.id == allocation_id).first()
    
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material allocation not found")
    
    # Find or create material issue template
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.workflow_type == WorkflowType.MATERIAL_ISSUE,
        WorkflowTemplate.is_active == True
    ).first()
    
    if not template:
        template = WorkflowTemplate(
            name="Material Issue Approval",
            code="MAT_ISSUE_APPROVAL",
            workflow_type=WorkflowType.MATERIAL_ISSUE,
            description="Material issue approval workflow",
            auto_approve_threshold=1000.0,
            sla_hours=24
        )
        db.add(template)
        db.flush()
        
        step = WorkflowStep(
            template_id=template.id,
            step_order=1,
            name="Store Supervisor Approval",
            approver_role=UserRole.HEAD_OF_OPERATIONS.value,
            is_mandatory=True
        )
        db.add(step)
        db.flush()
    
    # Estimate value (quantity * unit price if available)
    estimated_value = float(allocation.quantity_allocated or 0) * 100  # Default unit value
    
    instance = WorkflowInstance(
        template_id=template.id,
        reference_type="material_issue",
        reference_id=allocation.id,
        reference_number=f"MI-{allocation.id:05d}",
        amount=estimated_value,
        currency="USD",
        requested_by=current_user.id,
        status=WorkflowStatus.PENDING,
        current_step=1,
        notes=notes
    )
    db.add(instance)
    db.flush()
    
    for step in template.steps:
        approval = WorkflowApproval(
            workflow_instance_id=instance.id,
            workflow_step_id=step.id,
            step_number=step.step_order,
            status=ApprovalStatus.PENDING
        )
        db.add(approval)
    
    allocation.status = "pending_approval"
    
    log_audit(
        db, current_user, "SUBMIT", "material_allocation", allocation.id,
        f"Submitted material allocation {allocation.id} for approval",
        request=request
    )
    
    db.commit()
    db.refresh(instance)
    
    return instance


@router.post("/quality-inspection/{instance_id}/approve", response_model=WorkflowApprovalResponse)
def approve_quality_inspection(
    instance_id: int,
    passed: bool,
    inspection_notes: str,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_qa)
):
    """QA approval for material inspection."""
    instance = db.query(MaterialInstance).filter(MaterialInstance.id == instance_id).first()
    
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material instance not found")
    
    if instance.status != MaterialLifecycleStatus.IN_INSPECTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material is not in inspection status (current: {instance.status.value})"
        )
    
    old_status = instance.status.value
    
    if passed:
        instance.status = MaterialLifecycleStatus.IN_STORAGE
        instance.is_inspected = True
        instance.inspection_date = datetime.utcnow()
        instance.inspection_result = "passed"
    else:
        instance.status = MaterialLifecycleStatus.REJECTED
        instance.is_inspected = True
        instance.inspection_date = datetime.utcnow()
        instance.inspection_result = "failed"
    
    instance.inspection_notes = inspection_notes
    instance.inspected_by_id = current_user.id
    
    # Log status change
    status_history = MaterialStatusHistory(
        material_instance_id=instance.id,
        from_status=old_status,
        to_status=instance.status.value,
        changed_by_id=current_user.id,
        reason=inspection_notes,
        extra_data={"inspection_passed": passed}
    )
    db.add(status_history)
    
    log_audit(
        db, current_user, "INSPECT", "material_instance", instance.id,
        f"QA inspection {'passed' if passed else 'failed'}: {inspection_notes}",
        old_values={"status": old_status},
        new_values={"status": instance.status.value, "passed": passed},
        request=request
    )
    
    db.commit()
    
    return WorkflowApprovalResponse(
        id=0,
        workflow_instance_id=0,
        workflow_step_id=0,
        step_number=1,
        approver_id=current_user.id,
        status=ApprovalStatus.APPROVED if passed else ApprovalStatus.REJECTED,
        decision_at=datetime.utcnow(),
        comments=inspection_notes,
        is_escalated=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


# =============================================================================
# Pending Approvals Dashboard
# =============================================================================

@router.get("/my-approvals")
def get_my_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get all pending approvals for the current user."""
    # Get pending workflow approvals where user's role matches
    pending_approvals = db.query(WorkflowApproval).join(
        WorkflowInstance
    ).join(
        WorkflowStep
    ).filter(
        WorkflowApproval.status == ApprovalStatus.PENDING,
        WorkflowApproval.step_number == WorkflowInstance.current_step,
        or_(
            WorkflowStep.approver_user_id == current_user.id,
            WorkflowStep.approver_role == current_user.role.value
        )
    ).all()
    
    # Get pending POs if user is Director or Head of Operations
    pending_pos = []
    if current_user.role in [UserRole.DIRECTOR, UserRole.ADMIN, UserRole.HEAD_OF_OPERATIONS]:
        pending_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.status == POStatus.PENDING_APPROVAL
        ).all()
    
    # Get pending inspections if user is QA
    pending_inspections = []
    if current_user.role == UserRole.QA:
        pending_inspections = db.query(MaterialInstance).filter(
            MaterialInstance.status == MaterialLifecycleStatus.IN_INSPECTION
        ).all()
    
    return {
        "workflow_approvals": [
            {
                "approval_id": a.id,
                "instance_id": a.workflow_instance_id,
                "reference_type": a.workflow_instance.reference_type,
                "reference_number": a.workflow_instance.reference_number,
                "amount": float(a.workflow_instance.amount or 0),
                "currency": a.workflow_instance.currency,
                "requested_at": a.workflow_instance.requested_at.isoformat(),
                "priority": a.workflow_instance.priority
            }
            for a in pending_approvals
        ],
        "pending_pos": [
            {
                "id": po.id,
                "po_number": po.po_number,
                "total_amount": float(po.total_amount or 0),
                "currency": po.currency,
                "created_at": po.created_at.isoformat()
            }
            for po in pending_pos
        ],
        "pending_inspections": [
            {
                "id": mi.id,
                "item_number": mi.item_number,
                "material_id": mi.material_id,
                "quantity": float(mi.quantity or 0),
                "received_date": mi.received_date.isoformat() if mi.received_date else None
            }
            for mi in pending_inspections
        ],
        "total_pending": len(pending_approvals) + len(pending_pos) + len(pending_inspections)
    }


# =============================================================================
# Audit Trail Endpoints
# =============================================================================

@router.get("/audit-trail/{entity_type}/{entity_id}")
def get_audit_trail(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get audit trail for an entity."""
    logs = db.query(AuditLog).options(
        joinedload(AuditLog.user)
    ).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "user": log.user.full_name if log.user else None,
            "description": log.description,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "timestamp": log.created_at.isoformat(),
            "ip_address": log.ip_address
        }
        for log in logs
    ]
