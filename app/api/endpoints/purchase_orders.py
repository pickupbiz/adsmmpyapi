"""Purchase Order management endpoints with approval workflow."""
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.supplier import Supplier
from app.models.material import Material
from app.models.inventory import Inventory, InventoryStatus
from app.models.purchase_order import (
    PurchaseOrder, POLineItem, POApprovalHistory, 
    GoodsReceiptNote, GRNLineItem,
    POStatus, POPriority, ApprovalAction, MaterialStage, GRNStatus
)
from app.schemas.purchase_order import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, PurchaseOrderListResponse,
    POLineItemCreate, POLineItemUpdate, POLineItemResponse,
    POApprovalRequest, POApprovalHistoryResponse,
    GoodsReceiptNoteCreate, GoodsReceiptNoteUpdate, GoodsReceiptNoteResponse,
    GRNLineItemCreate, GRNLineItemUpdate, GRNLineItemResponse,
    MaterialLifecycleUpdate, POSummary,
    POStatusEnum, ApprovalActionEnum, MaterialStageEnum, GRNStatusEnum
)
from app.api.dependencies import (
    get_current_user, require_purchase, require_head_ops, require_director,
    require_store, require_qa, PaginationParams
)

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


# ============== Helper Functions ==============

def generate_po_number() -> str:
    """Generate unique PO number."""
    from datetime import datetime
    import secrets
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(3).upper()
    return f"PO-{timestamp}-{random_suffix}"


def generate_grn_number() -> str:
    """Generate unique GRN number."""
    from datetime import datetime
    import secrets
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(3).upper()
    return f"GRN-{timestamp}-{random_suffix}"


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_approval_required(po: PurchaseOrder, db: Session) -> bool:
    """Check if PO requires approval based on amount thresholds."""
    # Example: POs over $10,000 require Director approval
    # POs over $1,000 require Head of Operations approval
    return po.total_amount > 1000


# ============== Purchase Order CRUD ==============

@router.get("", response_model=dict)
def list_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(),
    status: Optional[POStatusEnum] = None,
    priority: Optional[str] = None,
    supplier_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None
):
    """List purchase orders with filtering and pagination."""
    query = db.query(PurchaseOrder)
    
    # Apply filters
    if status:
        query = query.filter(PurchaseOrder.status == status.value)
    if priority:
        query = query.filter(PurchaseOrder.priority == priority)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if from_date:
        query = query.filter(PurchaseOrder.po_date >= from_date)
    if to_date:
        query = query.filter(PurchaseOrder.po_date <= to_date)
    if search:
        query = query.filter(
            PurchaseOrder.po_number.ilike(f"%{search}%") |
            PurchaseOrder.requisition_number.ilike(f"%{search}%")
        )
    
    total = query.count()
    items = query.order_by(PurchaseOrder.created_at.desc()).offset(
        pagination.offset
    ).limit(pagination.limit).all()
    
    return {
        "items": [PurchaseOrderListResponse.model_validate(item) for item in items],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": (total + pagination.page_size - 1) // pagination.page_size
    }


@router.get("/summary", response_model=POSummary)
def get_po_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get PO summary statistics."""
    total_pos = db.query(PurchaseOrder).count()
    
    status_counts = db.query(
        PurchaseOrder.status,
        func.count(PurchaseOrder.id)
    ).group_by(PurchaseOrder.status).all()
    
    status_map = {s.value: c for s, c in status_counts}
    
    total_value = db.query(func.sum(PurchaseOrder.total_amount)).scalar() or 0
    
    pending_value = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.status.in_([POStatus.DRAFT, POStatus.PENDING_APPROVAL, POStatus.APPROVED])
    ).scalar() or 0
    
    return POSummary(
        total_pos=total_pos,
        draft_count=status_map.get("draft", 0),
        pending_approval_count=status_map.get("pending_approval", 0),
        approved_count=status_map.get("approved", 0),
        ordered_count=status_map.get("ordered", 0),
        received_count=status_map.get("received", 0),
        total_value=float(total_value),
        pending_value=float(pending_value)
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific purchase order by ID."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    return po


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Create a new purchase order."""
    # Validate supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == po_in.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with ID {po_in.supplier_id} does not exist"
        )
    
    # Create PO
    po_data = po_in.model_dump(exclude={"line_items"})
    po = PurchaseOrder(
        **po_data,
        po_number=generate_po_number(),
        created_by_id=current_user.id,
        status=POStatus.DRAFT
    )
    
    # Add line items
    for idx, item_data in enumerate(po_in.line_items, start=1):
        # Validate material exists
        material = db.query(Material).filter(Material.id == item_data.material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Material with ID {item_data.material_id} does not exist"
            )
        
        line_item = POLineItem(
            **item_data.model_dump(),
            line_number=idx,
            total_price=float(item_data.quantity_ordered) * float(item_data.unit_price) * (1 - item_data.discount_percent / 100)
        )
        po.line_items.append(line_item)
    
    # Calculate totals
    po.calculate_totals()
    
    db.add(po)
    db.commit()
    db.refresh(po)
    
    return po


@router.put("/{po_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    po_id: int,
    po_in: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Update a purchase order (only if in Draft status)."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update PO in '{po.status.value}' status. Only Draft POs can be updated."
        )
    
    # Update fields
    update_data = po_in.model_dump(exclude_unset=True)
    
    # Validate supplier if being changed
    if "supplier_id" in update_data:
        supplier = db.query(Supplier).filter(Supplier.id == update_data["supplier_id"]).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with ID {update_data['supplier_id']} does not exist"
            )
    
    for field, value in update_data.items():
        setattr(po, field, value)
    
    # Recalculate totals
    po.calculate_totals()
    po.revision_number += 1
    
    db.commit()
    db.refresh(po)
    
    return po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Delete a purchase order (only if in Draft status)."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete PO in '{po.status.value}' status. Only Draft POs can be deleted."
        )
    
    db.delete(po)
    db.commit()


# ============== PO Line Items ==============

@router.post("/{po_id}/items", response_model=POLineItemResponse, status_code=status.HTTP_201_CREATED)
def add_po_line_item(
    po_id: int,
    item_in: POLineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Add a line item to a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only add items to Draft POs"
        )
    
    # Validate material
    material = db.query(Material).filter(Material.id == item_in.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material with ID {item_in.material_id} does not exist"
        )
    
    # Get next line number
    max_line = db.query(func.max(POLineItem.line_number)).filter(
        POLineItem.purchase_order_id == po_id
    ).scalar() or 0
    
    line_item = POLineItem(
        **item_in.model_dump(),
        purchase_order_id=po_id,
        line_number=max_line + 1,
        total_price=float(item_in.quantity_ordered) * float(item_in.unit_price) * (1 - item_in.discount_percent / 100)
    )
    
    db.add(line_item)
    po.calculate_totals()
    po.revision_number += 1
    
    db.commit()
    db.refresh(line_item)
    
    return line_item


@router.put("/{po_id}/items/{item_id}", response_model=POLineItemResponse)
def update_po_line_item(
    po_id: int,
    item_id: int,
    item_in: POLineItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Update a PO line item."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update items in Draft POs"
        )
    
    line_item = db.query(POLineItem).filter(
        POLineItem.id == item_id,
        POLineItem.purchase_order_id == po_id
    ).first()
    
    if not line_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line item not found"
        )
    
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(line_item, field, value)
    
    # Recalculate line total
    line_item.calculate_total()
    po.calculate_totals()
    po.revision_number += 1
    
    db.commit()
    db.refresh(line_item)
    
    return line_item


@router.delete("/{po_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_po_line_item(
    po_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Delete a PO line item."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete items from Draft POs"
        )
    
    line_item = db.query(POLineItem).filter(
        POLineItem.id == item_id,
        POLineItem.purchase_order_id == po_id
    ).first()
    
    if not line_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line item not found"
        )
    
    db.delete(line_item)
    po.calculate_totals()
    po.revision_number += 1
    
    db.commit()


# ============== PO Approval Workflow ==============

@router.post("/{po_id}/submit", response_model=PurchaseOrderResponse)
def submit_po_for_approval(
    po_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Submit a PO for approval."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit PO in '{po.status.value}' status"
        )
    
    if not po.line_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit PO without line items"
        )
    
    old_status = po.status
    po.status = POStatus.PENDING_APPROVAL
    
    # Log approval history
    history = POApprovalHistory(
        purchase_order_id=po.id,
        user_id=current_user.id,
        action=ApprovalAction.SUBMITTED,
        from_status=old_status,
        to_status=po.status,
        comments="Submitted for approval",
        po_total_at_action=po.total_amount,
        po_revision_at_action=po.revision_number,
        ip_address=get_client_ip(request)
    )
    
    db.add(history)
    db.commit()
    db.refresh(po)
    
    return po


@router.post("/{po_id}/approve", response_model=PurchaseOrderResponse)
def approve_purchase_order(
    po_id: int,
    approval_in: POApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_head_ops)
):
    """Approve or reject a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve/reject PO in '{po.status.value}' status"
        )
    
    # Check approval authority
    if po.total_amount > 10000 and not current_user.is_superuser:
        # High value POs need Director approval
        from app.models.user import UserRole
        if current_user.role not in [UserRole.DIRECTOR, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"POs over $10,000 require Director approval"
            )
    
    old_status = po.status
    
    if approval_in.action == ApprovalActionEnum.APPROVED:
        po.status = POStatus.APPROVED
        po.approved_by_id = current_user.id
        po.approved_date = datetime.utcnow()
        po.approval_notes = approval_in.comments
    elif approval_in.action == ApprovalActionEnum.REJECTED:
        po.status = POStatus.REJECTED
        po.rejection_reason = approval_in.comments
    elif approval_in.action == ApprovalActionEnum.RETURNED:
        po.status = POStatus.DRAFT
        po.approval_notes = f"Returned for revision: {approval_in.comments}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid approval action: {approval_in.action}"
        )
    
    # Log approval history
    history = POApprovalHistory(
        purchase_order_id=po.id,
        user_id=current_user.id,
        action=ApprovalAction(approval_in.action.value),
        from_status=old_status,
        to_status=po.status,
        comments=approval_in.comments,
        po_total_at_action=po.total_amount,
        po_revision_at_action=po.revision_number,
        ip_address=get_client_ip(request)
    )
    
    db.add(history)
    db.commit()
    db.refresh(po)
    
    return po


@router.post("/{po_id}/order", response_model=PurchaseOrderResponse)
def mark_po_as_ordered(
    po_id: int,
    request: Request,
    tracking_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_purchase)
):
    """Mark an approved PO as ordered (sent to supplier)."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status != POStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only mark approved POs as ordered"
        )
    
    old_status = po.status
    po.status = POStatus.ORDERED
    po.ordered_date = date.today()
    if tracking_number:
        po.tracking_number = tracking_number
    
    # Update line items to "on_order" stage
    for item in po.line_items:
        item.material_stage = MaterialStage.ON_ORDER
    
    # Log history
    history = POApprovalHistory(
        purchase_order_id=po.id,
        user_id=current_user.id,
        action=ApprovalAction.APPROVED,  # Using approved as generic "action taken"
        from_status=old_status,
        to_status=po.status,
        comments="PO sent to supplier",
        po_total_at_action=po.total_amount,
        po_revision_at_action=po.revision_number,
        ip_address=get_client_ip(request)
    )
    
    db.add(history)
    db.commit()
    db.refresh(po)
    
    return po


@router.post("/{po_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_purchase_order(
    po_id: int,
    request: Request,
    reason: str = Query(..., description="Cancellation reason"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_head_ops)
):
    """Cancel a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status in [POStatus.RECEIVED, POStatus.CLOSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel PO in '{po.status.value}' status"
        )
    
    old_status = po.status
    po.status = POStatus.CANCELLED
    po.rejection_reason = reason
    
    # Log history
    history = POApprovalHistory(
        purchase_order_id=po.id,
        user_id=current_user.id,
        action=ApprovalAction.CANCELLED,
        from_status=old_status,
        to_status=po.status,
        comments=reason,
        po_total_at_action=po.total_amount,
        po_revision_at_action=po.revision_number,
        ip_address=get_client_ip(request)
    )
    
    db.add(history)
    db.commit()
    db.refresh(po)
    
    return po


@router.get("/{po_id}/history", response_model=List[POApprovalHistoryResponse])
def get_po_approval_history(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get approval history for a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    return po.approval_history


# ============== Goods Receipt Notes ==============

@router.post("/{po_id}/receive", response_model=GoodsReceiptNoteResponse, status_code=status.HTTP_201_CREATED)
def create_goods_receipt(
    po_id: int,
    grn_in: GoodsReceiptNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Create a Goods Receipt Note for received materials."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if po.status not in [POStatus.ORDERED, POStatus.PARTIALLY_RECEIVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive against PO in '{po.status.value}' status"
        )
    
    # Create GRN
    grn_data = grn_in.model_dump(exclude={"line_items"})
    grn = GoodsReceiptNote(
        **grn_data,
        grn_number=generate_grn_number(),
        received_by_id=current_user.id,
        status=GRNStatus.DRAFT
    )
    
    # Add line items and update PO quantities
    for item_data in grn_in.line_items:
        po_line = db.query(POLineItem).filter(
            POLineItem.id == item_data.po_line_item_id,
            POLineItem.purchase_order_id == po_id
        ).first()
        
        if not po_line:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PO line item {item_data.po_line_item_id} not found"
            )
        
        # Check if receiving more than ordered
        total_received = float(po_line.quantity_received) + float(item_data.quantity_received)
        if total_received > float(po_line.quantity_ordered) * 1.1:  # Allow 10% overage
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total received ({total_received}) exceeds ordered quantity ({po_line.quantity_ordered})"
            )
        
        grn_line = GRNLineItem(**item_data.model_dump())
        grn.line_items.append(grn_line)
        
        # Update PO line item quantities
        po_line.quantity_received = total_received
        po_line.material_stage = MaterialStage.IN_INSPECTION
    
    # Update PO status
    all_received = all(
        float(item.quantity_received) >= float(item.quantity_ordered)
        for item in po.line_items
    )
    
    if all_received:
        po.status = POStatus.RECEIVED
    else:
        po.status = POStatus.PARTIALLY_RECEIVED
    
    db.add(grn)
    db.commit()
    db.refresh(grn)
    
    return grn


@router.get("/{po_id}/receipts", response_model=List[GoodsReceiptNoteResponse])
def list_goods_receipts(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all goods receipts for a purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    return po.goods_receipts


@router.get("/grn/{grn_id}", response_model=GoodsReceiptNoteResponse)
def get_goods_receipt(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific Goods Receipt Note."""
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goods Receipt Note not found"
        )
    return grn


@router.post("/grn/{grn_id}/inspect", response_model=GoodsReceiptNoteResponse)
def complete_grn_inspection(
    grn_id: int,
    inspection_passed: bool,
    inspection_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_qa)
):
    """Complete QA inspection for a GRN."""
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goods Receipt Note not found"
        )
    
    if grn.status not in [GRNStatus.DRAFT, GRNStatus.PENDING_INSPECTION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot inspect GRN in '{grn.status.value}' status"
        )
    
    grn.inspected_by_id = current_user.id
    grn.inspection_date = date.today()
    grn.inspection_notes = inspection_notes
    
    if inspection_passed:
        grn.status = GRNStatus.INSPECTION_PASSED
        # Update line items to RAW_MATERIAL stage
        for line in grn.line_items:
            line.inspection_status = "passed"
            line.quantity_accepted = line.quantity_received
            
            # Update PO line item stage
            po_line = line.po_line_item
            po_line.quantity_accepted += float(line.quantity_accepted)
            po_line.material_stage = MaterialStage.RAW_MATERIAL
    else:
        grn.status = GRNStatus.INSPECTION_FAILED
        for line in grn.line_items:
            line.inspection_status = "failed"
            line.quantity_rejected = line.quantity_received
            
            # Update PO line item
            po_line = line.po_line_item
            po_line.quantity_rejected += float(line.quantity_rejected)
    
    db.commit()
    db.refresh(grn)
    
    return grn


@router.post("/grn/{grn_id}/accept", response_model=GoodsReceiptNoteResponse)
def accept_grn_to_inventory(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Accept GRN materials into inventory."""
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goods Receipt Note not found"
        )
    
    if grn.status != GRNStatus.INSPECTION_PASSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only accept GRNs that passed inspection"
        )
    
    # Create inventory records for each line item
    for line in grn.line_items:
        if line.quantity_accepted > 0:
            po_line = line.po_line_item
            
            # Create inventory record
            inventory = Inventory(
                material_id=po_line.material_id,
                lot_number=line.lot_number,
                batch_number=line.batch_number,
                quantity=float(line.quantity_accepted),
                unit_of_measure=line.unit_of_measure,
                status=InventoryStatus.AVAILABLE,
                location=line.storage_location or grn.storage_location,
                bin_number=line.bin_number,
                received_date=grn.receipt_date,
                manufacture_date=line.manufacture_date,
                expiration_date=line.expiry_date,
                heat_number=line.heat_number,
                certificate_of_conformance=f"GRN-{grn.grn_number}",
                notes=f"Received via GRN {grn.grn_number} from PO {grn.purchase_order.po_number}"
            )
            
            db.add(inventory)
            db.flush()  # Get the inventory ID
            
            # Link GRN line to inventory
            line.inventory_id = inventory.id
    
    grn.status = GRNStatus.ACCEPTED
    
    db.commit()
    db.refresh(grn)
    
    return grn


# ============== Material Lifecycle ==============

@router.put("/{po_id}/items/{item_id}/stage", response_model=POLineItemResponse)
def update_material_stage(
    po_id: int,
    item_id: int,
    stage_update: MaterialLifecycleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Update the material lifecycle stage for a PO line item."""
    line_item = db.query(POLineItem).filter(
        POLineItem.id == item_id,
        POLineItem.purchase_order_id == po_id
    ).first()
    
    if not line_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PO line item not found"
        )
    
    # Validate stage transition
    valid_transitions = {
        MaterialStage.ON_ORDER: [MaterialStage.IN_INSPECTION, MaterialStage.RAW_MATERIAL],
        MaterialStage.IN_INSPECTION: [MaterialStage.RAW_MATERIAL, MaterialStage.SCRAPPED],
        MaterialStage.RAW_MATERIAL: [MaterialStage.WIP, MaterialStage.CONSUMED],
        MaterialStage.WIP: [MaterialStage.FINISHED_GOODS, MaterialStage.SCRAPPED],
        MaterialStage.FINISHED_GOODS: [MaterialStage.CONSUMED, MaterialStage.SCRAPPED],
    }
    
    current_stage = line_item.material_stage
    new_stage = MaterialStage(stage_update.material_stage.value)
    
    if new_stage not in valid_transitions.get(current_stage, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage transition from '{current_stage.value}' to '{new_stage.value}'"
        )
    
    line_item.material_stage = new_stage
    if stage_update.notes:
        line_item.notes = (line_item.notes or "") + f"\n[{datetime.now().isoformat()}] Stage: {new_stage.value} - {stage_update.notes}"
    
    db.commit()
    db.refresh(line_item)
    
    return line_item
