"""Material Instance management endpoints with PO integration."""
from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from app.db.session import get_db
from app.models.user import User
from app.models.material import Material
from app.models.supplier import Supplier
from app.models.material_instance import (
    MaterialInstance, MaterialAllocation, MaterialStatusHistory, 
    BOMSourceTracking, MaterialLifecycleStatus, MaterialCondition
)
from app.models.purchase_order import (
    PurchaseOrder, POLineItem, GoodsReceiptNote, GRNLineItem,
    POStatus, MaterialStage, GRNStatus
)
from app.models.project import Project, BillOfMaterials, BOMItem
from app.schemas.material_instance import (
    MaterialInstanceCreate, MaterialInstanceUpdate, MaterialInstanceResponse,
    MaterialInstanceDetailResponse, MaterialInstanceFromGRN,
    MaterialStatusChangeRequest, MaterialStatusHistoryResponse,
    MaterialAllocationCreate, MaterialAllocationUpdate, MaterialAllocationResponse,
    MaterialIssueRequest, MaterialReturnRequest,
    BOMSourceTrackingCreate, BOMSourceTrackingUpdate, BOMSourceTrackingResponse,
    MaterialReceiptFromPORequest, BulkMaterialReceiptRequest,
    MaterialInspectionRequest, ProjectMaterialSummary, BOMSourceSummary,
    MaterialLifecycleReport, MaterialInventorySummary,
    MaterialLifecycleStatus as SchemaLifecycleStatus
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    get_current_user, require_store, require_qa, require_engineer,
    require_any_role, PaginationParams
)


router = APIRouter(prefix="/material-instances", tags=["Material Instances"])


# =============================================================================
# Helper Functions
# =============================================================================

def generate_item_number(db: Session) -> str:
    """Generate unique item number for material instance."""
    today = date.today()
    prefix = f"MI-{today.strftime('%Y%m')}"
    
    # Find the last item number with this prefix
    last_item = db.query(MaterialInstance).filter(
        MaterialInstance.item_number.like(f"{prefix}%")
    ).order_by(MaterialInstance.item_number.desc()).first()
    
    if last_item:
        last_num = int(last_item.item_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"{prefix}-{new_num:05d}"


def generate_allocation_number(db: Session) -> str:
    """Generate unique allocation number."""
    today = date.today()
    prefix = f"ALLOC-{today.strftime('%Y%m')}"
    
    last_alloc = db.query(MaterialAllocation).filter(
        MaterialAllocation.allocation_number.like(f"{prefix}%")
    ).order_by(MaterialAllocation.allocation_number.desc()).first()
    
    if last_alloc:
        last_num = int(last_alloc.allocation_number.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"{prefix}-{new_num:05d}"


def record_status_change(
    db: Session,
    material_instance: MaterialInstance,
    from_status: Optional[MaterialLifecycleStatus],
    to_status: MaterialLifecycleStatus,
    user: User,
    reference_type: Optional[str] = None,
    reference_number: Optional[str] = None,
    reason: Optional[str] = None,
    notes: Optional[str] = None
) -> MaterialStatusHistory:
    """Record material status change in history."""
    history = MaterialStatusHistory(
        material_instance_id=material_instance.id,
        from_status=from_status,
        to_status=to_status,
        changed_by_id=user.id,
        reference_type=reference_type,
        reference_number=reference_number,
        reason=reason,
        notes=notes
    )
    db.add(history)
    return history


# =============================================================================
# Material Instance CRUD Endpoints
# =============================================================================

@router.get("", response_model=PaginatedResponse[MaterialInstanceResponse])
def list_material_instances(
    pagination: PaginationParams = Depends(),
    lifecycle_status: Optional[SchemaLifecycleStatus] = Query(None),
    condition: Optional[MaterialCondition] = Query(None),
    material_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    purchase_order_id: Optional[int] = Query(None),
    storage_location: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by item number, lot, batch, serial, or heat number"),
    available_only: bool = Query(False, description="Show only available materials"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    List material instances with filtering options.
    
    - **lifecycle_status**: Filter by lifecycle status
    - **condition**: Filter by material condition
    - **material_id**: Filter by material master
    - **supplier_id**: Filter by supplier
    - **purchase_order_id**: Filter by source PO
    - **storage_location**: Filter by storage location
    - **search**: Search across multiple fields
    - **available_only**: Show only materials available for allocation
    """
    query = db.query(MaterialInstance)
    
    if lifecycle_status:
        query = query.filter(MaterialInstance.lifecycle_status == lifecycle_status.value)
    if condition:
        query = query.filter(MaterialInstance.condition == condition)
    if material_id:
        query = query.filter(MaterialInstance.material_id == material_id)
    if supplier_id:
        query = query.filter(MaterialInstance.supplier_id == supplier_id)
    if purchase_order_id:
        query = query.filter(MaterialInstance.purchase_order_id == purchase_order_id)
    if storage_location:
        query = query.filter(MaterialInstance.storage_location.ilike(f"%{storage_location}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (MaterialInstance.item_number.ilike(search_term)) |
            (MaterialInstance.lot_number.ilike(search_term)) |
            (MaterialInstance.batch_number.ilike(search_term)) |
            (MaterialInstance.serial_number.ilike(search_term)) |
            (MaterialInstance.heat_number.ilike(search_term)) |
            (MaterialInstance.title.ilike(search_term))
        )
    if available_only:
        query = query.filter(
            MaterialInstance.lifecycle_status == MaterialLifecycleStatus.IN_STORAGE,
            (MaterialInstance.quantity - MaterialInstance.reserved_quantity - MaterialInstance.issued_quantity) > 0
        )
    
    total = query.count()
    instances = query.order_by(MaterialInstance.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=instances,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{instance_id}", response_model=MaterialInstanceDetailResponse)
def get_material_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get material instance details by ID."""
    instance = db.query(MaterialInstance).options(
        joinedload(MaterialInstance.material),
        joinedload(MaterialInstance.supplier),
        joinedload(MaterialInstance.purchase_order)
    ).filter(MaterialInstance.id == instance_id).first()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    # Build response with additional details
    response = MaterialInstanceDetailResponse.model_validate(instance)
    if instance.material:
        response.material_name = instance.material.name
        response.material_part_number = instance.material.part_number
    if instance.supplier:
        response.supplier_name = instance.supplier.name
    if instance.purchase_order:
        response.po_number = instance.purchase_order.po_number
    
    return response


@router.post("", response_model=MaterialInstanceResponse, status_code=status.HTTP_201_CREATED)
def create_material_instance(
    instance_in: MaterialInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """
    Create a new material instance (direct entry without PO).
    For PO-based receipt, use the /receive-from-po endpoint.
    """
    # Validate material exists
    material = db.query(Material).filter(Material.id == instance_in.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material not found"
        )
    
    # Validate supplier if provided
    if instance_in.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == instance_in.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier not found"
            )
    
    # Generate item number
    item_number = generate_item_number(db)
    
    # Determine initial status
    initial_status = MaterialLifecycleStatus.RECEIVED
    if instance_in.purchase_order_id:
        initial_status = MaterialLifecycleStatus.ORDERED
    
    instance_data = instance_in.model_dump()
    instance_data["item_number"] = item_number
    instance_data["lifecycle_status"] = initial_status
    instance_data["received_by_id"] = current_user.id
    
    instance = MaterialInstance(**instance_data)
    db.add(instance)
    db.flush()
    
    # Record status history
    record_status_change(
        db, instance, None, initial_status, current_user,
        notes="Material instance created"
    )
    
    db.commit()
    db.refresh(instance)
    return instance


@router.put("/{instance_id}", response_model=MaterialInstanceResponse)
def update_material_instance(
    instance_id: int,
    instance_in: MaterialInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Update material instance details."""
    instance = db.query(MaterialInstance).filter(MaterialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    update_data = instance_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(instance, field, value)
    
    db.commit()
    db.refresh(instance)
    return instance


@router.delete("/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Delete a material instance (only if no allocations exist)."""
    instance = db.query(MaterialInstance).filter(MaterialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    # Check for active allocations
    active_allocations = db.query(MaterialAllocation).filter(
        MaterialAllocation.material_instance_id == instance_id,
        MaterialAllocation.is_active == True
    ).count()
    
    if active_allocations > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete material instance with active allocations"
        )
    
    db.delete(instance)
    db.commit()


# =============================================================================
# Material Receipt from PO/GRN Endpoints
# =============================================================================

@router.post("/receive-from-grn", response_model=List[MaterialInstanceResponse])
def receive_materials_from_grn(
    receipt: MaterialInstanceFromGRN,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """
    Create material instance from GRN line item.
    Links the material to the source PO and updates quantities.
    """
    # Get GRN line item with related data
    grn_item = db.query(GRNLineItem).options(
        joinedload(GRNLineItem.goods_receipt).joinedload(GoodsReceiptNote.purchase_order),
        joinedload(GRNLineItem.po_line_item).joinedload(POLineItem.material)
    ).filter(GRNLineItem.id == receipt.grn_line_item_id).first()
    
    if not grn_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN line item not found"
        )
    
    grn = grn_item.goods_receipt
    po = grn.purchase_order
    po_line = grn_item.po_line_item
    material = po_line.material
    
    # Generate item number
    item_number = generate_item_number(db)
    
    # Create material instance
    instance = MaterialInstance(
        item_number=item_number,
        title=receipt.title,
        material_id=material.id,
        purchase_order_id=po.id,
        po_line_item_id=po_line.id,
        grn_line_item_id=grn_item.id,
        supplier_id=po.supplier_id,
        specification=receipt.specification or po_line.specification,
        revision=receipt.revision or po_line.revision,
        quantity=grn_item.quantity_accepted or grn_item.quantity_received,
        unit_of_measure=grn_item.unit_of_measure,
        unit_cost=float(po_line.unit_price) if po_line.unit_price else None,
        lot_number=receipt.lot_number or grn_item.lot_number,
        batch_number=receipt.batch_number or grn_item.batch_number,
        serial_number=receipt.serial_number,
        heat_number=receipt.heat_number or grn_item.heat_number,
        lifecycle_status=MaterialLifecycleStatus.IN_INSPECTION if grn.status == GRNStatus.PENDING_INSPECTION else MaterialLifecycleStatus.IN_STORAGE,
        condition=MaterialCondition.NEW,
        order_date=po.po_date,
        received_date=grn.receipt_date,
        manufacture_date=receipt.manufacture_date or grn_item.manufacture_date,
        expiry_date=receipt.expiry_date or grn_item.expiry_date,
        storage_location=receipt.storage_location or grn_item.storage_location,
        bin_number=receipt.bin_number or grn_item.bin_number,
        certificate_number=receipt.certificate_number,
        certificate_received=grn.coc_received,
        po_reference=po.po_number,
        received_by_id=current_user.id,
        notes=receipt.notes
    )
    
    db.add(instance)
    db.flush()
    
    # Record status history
    initial_status = MaterialLifecycleStatus.IN_INSPECTION if grn.status == GRNStatus.PENDING_INSPECTION else MaterialLifecycleStatus.IN_STORAGE
    record_status_change(
        db, instance, None, initial_status, current_user,
        reference_type="GRN",
        reference_number=grn.grn_number,
        notes=f"Received from PO {po.po_number}"
    )
    
    # Link GRN item to inventory (via material instance)
    grn_item.inventory_id = instance.id  # This will need schema adjustment
    
    # Update PO line item stage
    po_line.material_stage = MaterialStage.RAW_MATERIAL if initial_status == MaterialLifecycleStatus.IN_STORAGE else MaterialStage.IN_INSPECTION
    
    db.commit()
    db.refresh(instance)
    
    return [instance]


@router.post("/bulk-receive", response_model=List[MaterialInstanceResponse])
def bulk_receive_materials(
    receipts: List[MaterialInstanceFromGRN],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Bulk receive multiple materials from GRN items."""
    instances = []
    
    for receipt in receipts:
        grn_item = db.query(GRNLineItem).options(
            joinedload(GRNLineItem.goods_receipt).joinedload(GoodsReceiptNote.purchase_order),
            joinedload(GRNLineItem.po_line_item).joinedload(POLineItem.material)
        ).filter(GRNLineItem.id == receipt.grn_line_item_id).first()
        
        if not grn_item:
            continue
        
        grn = grn_item.goods_receipt
        po = grn.purchase_order
        po_line = grn_item.po_line_item
        material = po_line.material
        
        item_number = generate_item_number(db)
        
        instance = MaterialInstance(
            item_number=item_number,
            title=receipt.title,
            material_id=material.id,
            purchase_order_id=po.id,
            po_line_item_id=po_line.id,
            grn_line_item_id=grn_item.id,
            supplier_id=po.supplier_id,
            specification=receipt.specification or po_line.specification,
            revision=receipt.revision or po_line.revision,
            quantity=grn_item.quantity_accepted or grn_item.quantity_received,
            unit_of_measure=grn_item.unit_of_measure,
            unit_cost=float(po_line.unit_price) if po_line.unit_price else None,
            lot_number=receipt.lot_number or grn_item.lot_number,
            batch_number=receipt.batch_number or grn_item.batch_number,
            heat_number=receipt.heat_number or grn_item.heat_number,
            lifecycle_status=MaterialLifecycleStatus.IN_STORAGE,
            condition=MaterialCondition.NEW,
            order_date=po.po_date,
            received_date=grn.receipt_date,
            manufacture_date=receipt.manufacture_date or grn_item.manufacture_date,
            expiry_date=receipt.expiry_date or grn_item.expiry_date,
            storage_location=receipt.storage_location or grn_item.storage_location,
            bin_number=receipt.bin_number or grn_item.bin_number,
            po_reference=po.po_number,
            received_by_id=current_user.id,
            notes=receipt.notes
        )
        
        db.add(instance)
        db.flush()
        
        record_status_change(
            db, instance, None, MaterialLifecycleStatus.IN_STORAGE, current_user,
            reference_type="GRN",
            reference_number=grn.grn_number,
            notes=f"Bulk received from PO {po.po_number}"
        )
        
        instances.append(instance)
    
    db.commit()
    
    for inst in instances:
        db.refresh(inst)
    
    return instances


# =============================================================================
# Material Status Management Endpoints
# =============================================================================

@router.post("/{instance_id}/change-status", response_model=MaterialInstanceResponse)
def change_material_status(
    instance_id: int,
    status_change: MaterialStatusChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """
    Change material instance lifecycle status.
    
    Valid transitions:
    - RECEIVED → IN_INSPECTION
    - IN_INSPECTION → IN_STORAGE (passed) or REJECTED (failed)
    - IN_STORAGE → RESERVED, ISSUED, SCRAPPED
    - RESERVED → ISSUED, IN_STORAGE (release)
    - ISSUED → IN_PRODUCTION, IN_STORAGE (return)
    - IN_PRODUCTION → COMPLETED, SCRAPPED
    """
    instance = db.query(MaterialInstance).filter(MaterialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    from_status = instance.lifecycle_status
    to_status_enum = MaterialLifecycleStatus(status_change.new_status.value)
    
    # Validate status transition
    valid_transitions = {
        MaterialLifecycleStatus.ORDERED: [MaterialLifecycleStatus.RECEIVED],
        MaterialLifecycleStatus.RECEIVED: [MaterialLifecycleStatus.IN_INSPECTION, MaterialLifecycleStatus.IN_STORAGE],
        MaterialLifecycleStatus.IN_INSPECTION: [MaterialLifecycleStatus.IN_STORAGE, MaterialLifecycleStatus.REJECTED],
        MaterialLifecycleStatus.IN_STORAGE: [MaterialLifecycleStatus.RESERVED, MaterialLifecycleStatus.ISSUED, MaterialLifecycleStatus.SCRAPPED, MaterialLifecycleStatus.RETURNED],
        MaterialLifecycleStatus.RESERVED: [MaterialLifecycleStatus.ISSUED, MaterialLifecycleStatus.IN_STORAGE],
        MaterialLifecycleStatus.ISSUED: [MaterialLifecycleStatus.IN_PRODUCTION, MaterialLifecycleStatus.IN_STORAGE],
        MaterialLifecycleStatus.IN_PRODUCTION: [MaterialLifecycleStatus.COMPLETED, MaterialLifecycleStatus.SCRAPPED],
    }
    
    allowed = valid_transitions.get(from_status, [])
    if to_status_enum not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {from_status.value} to {to_status_enum.value}. Allowed: {[s.value for s in allowed]}"
        )
    
    # Update status
    instance.lifecycle_status = to_status_enum
    
    # Handle specific status changes
    if to_status_enum == MaterialLifecycleStatus.IN_INSPECTION:
        instance.inspection_date = date.today()
    elif to_status_enum == MaterialLifecycleStatus.IN_STORAGE:
        if status_change.storage_location:
            instance.storage_location = status_change.storage_location
        if status_change.bin_number:
            instance.bin_number = status_change.bin_number
        if status_change.inspection_passed is not None:
            instance.inspection_passed = status_change.inspection_passed
        if status_change.inspection_notes:
            instance.inspection_notes = status_change.inspection_notes
    elif to_status_enum == MaterialLifecycleStatus.REJECTED:
        instance.inspection_passed = False
        if status_change.inspection_notes:
            instance.inspection_notes = status_change.inspection_notes
    
    # Record status change
    record_status_change(
        db, instance, from_status, to_status_enum, current_user,
        reference_type=status_change.reference_type,
        reference_number=status_change.reference_number,
        reason=status_change.reason,
        notes=status_change.notes
    )
    
    db.commit()
    db.refresh(instance)
    return instance


@router.post("/{instance_id}/inspect", response_model=MaterialInstanceResponse)
def inspect_material(
    instance_id: int,
    inspection: MaterialInspectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_qa)
):
    """
    Process material inspection (QA role required).
    Updates status based on inspection result.
    """
    instance = db.query(MaterialInstance).filter(MaterialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    if instance.lifecycle_status not in [MaterialLifecycleStatus.RECEIVED, MaterialLifecycleStatus.IN_INSPECTION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material must be in RECEIVED or IN_INSPECTION status for inspection"
        )
    
    from_status = instance.lifecycle_status
    
    # Update inspection fields
    instance.inspection_passed = inspection.inspection_passed
    instance.inspection_notes = inspection.inspection_notes
    instance.inspection_date = date.today()
    instance.inspected_by_id = current_user.id
    
    if inspection.inspection_passed:
        instance.lifecycle_status = MaterialLifecycleStatus.IN_STORAGE
        if inspection.storage_location:
            instance.storage_location = inspection.storage_location
        if inspection.bin_number:
            instance.bin_number = inspection.bin_number
        
        # Update PO line item stage
        if instance.po_line_item_id:
            po_line = db.query(POLineItem).filter(POLineItem.id == instance.po_line_item_id).first()
            if po_line:
                po_line.material_stage = MaterialStage.RAW_MATERIAL
                po_line.inspection_completed = True
    else:
        instance.lifecycle_status = MaterialLifecycleStatus.REJECTED
        
        # Update PO line item
        if instance.po_line_item_id:
            po_line = db.query(POLineItem).filter(POLineItem.id == instance.po_line_item_id).first()
            if po_line:
                po_line.material_stage = MaterialStage.SCRAPPED
    
    record_status_change(
        db, instance, from_status, instance.lifecycle_status, current_user,
        reference_type="INSPECTION",
        reason="Inspection completed" if inspection.inspection_passed else f"Inspection failed: {inspection.rejection_reason}",
        notes=inspection.inspection_notes
    )
    
    db.commit()
    db.refresh(instance)
    return instance


@router.get("/{instance_id}/history", response_model=List[MaterialStatusHistoryResponse])
def get_material_status_history(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get material instance status change history."""
    instance = db.query(MaterialInstance).filter(MaterialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    history = db.query(MaterialStatusHistory).options(
        joinedload(MaterialStatusHistory.changed_by)
    ).filter(
        MaterialStatusHistory.material_instance_id == instance_id
    ).order_by(MaterialStatusHistory.created_at.desc()).all()
    
    result = []
    for h in history:
        item = MaterialStatusHistoryResponse.model_validate(h)
        if h.changed_by:
            item.changed_by_name = h.changed_by.full_name
        result.append(item)
    
    return result


# =============================================================================
# Material Allocation Endpoints
# =============================================================================

@router.post("/allocations", response_model=MaterialAllocationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(
    allocation_in: MaterialAllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """
    Allocate material to a project, BOM, or work order.
    Reserves quantity for the specified target.
    """
    # Validate material instance exists and is available
    instance = db.query(MaterialInstance).filter(
        MaterialInstance.id == allocation_in.material_instance_id
    ).first()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    if instance.lifecycle_status != MaterialLifecycleStatus.IN_STORAGE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material must be IN_STORAGE status for allocation"
        )
    
    # Check available quantity
    available = float(instance.quantity) - float(instance.reserved_quantity) - float(instance.issued_quantity)
    if allocation_in.quantity_allocated > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient quantity. Available: {available}, Requested: {allocation_in.quantity_allocated}"
        )
    
    # Validate allocation target
    if not any([allocation_in.project_id, allocation_in.bom_id, allocation_in.work_order_reference]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify at least one allocation target (project_id, bom_id, or work_order_reference)"
        )
    
    if allocation_in.project_id:
        project = db.query(Project).filter(Project.id == allocation_in.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found"
            )
    
    if allocation_in.bom_id:
        bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == allocation_in.bom_id).first()
        if not bom:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="BOM not found"
            )
    
    # Generate allocation number
    allocation_number = generate_allocation_number(db)
    
    # Create allocation
    allocation = MaterialAllocation(
        allocation_number=allocation_number,
        material_instance_id=instance.id,
        project_id=allocation_in.project_id,
        bom_id=allocation_in.bom_id,
        work_order_reference=allocation_in.work_order_reference,
        quantity_allocated=allocation_in.quantity_allocated,
        unit_of_measure=allocation_in.unit_of_measure,
        required_date=allocation_in.required_date,
        priority=allocation_in.priority,
        allocated_by_id=current_user.id,
        notes=allocation_in.notes
    )
    
    # Update material instance reserved quantity
    instance.reserved_quantity = float(instance.reserved_quantity) + allocation_in.quantity_allocated
    
    # Update status if fully reserved
    if instance.available_quantity <= 0:
        old_status = instance.lifecycle_status
        instance.lifecycle_status = MaterialLifecycleStatus.RESERVED
        record_status_change(
            db, instance, old_status, MaterialLifecycleStatus.RESERVED, current_user,
            reference_type="ALLOCATION",
            reference_number=allocation_number,
            notes="Fully allocated"
        )
    
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


@router.get("/allocations", response_model=PaginatedResponse[MaterialAllocationResponse])
def list_allocations(
    pagination: PaginationParams = Depends(),
    material_instance_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    bom_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List material allocations with filtering."""
    query = db.query(MaterialAllocation)
    
    if material_instance_id:
        query = query.filter(MaterialAllocation.material_instance_id == material_instance_id)
    if project_id:
        query = query.filter(MaterialAllocation.project_id == project_id)
    if bom_id:
        query = query.filter(MaterialAllocation.bom_id == bom_id)
    if active_only:
        query = query.filter(MaterialAllocation.is_active == True)
    
    total = query.count()
    allocations = query.order_by(MaterialAllocation.priority, MaterialAllocation.required_date).offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=allocations,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.post("/allocations/{allocation_id}/issue", response_model=MaterialAllocationResponse)
def issue_allocated_material(
    allocation_id: int,
    issue_request: MaterialIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Issue allocated material to production/project."""
    allocation = db.query(MaterialAllocation).filter(
        MaterialAllocation.id == allocation_id
    ).first()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found"
        )
    
    if not allocation.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allocation is not active"
        )
    
    # Check outstanding quantity
    outstanding = float(allocation.quantity_allocated) - float(allocation.quantity_issued)
    if issue_request.quantity_to_issue > outstanding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot issue more than outstanding. Outstanding: {outstanding}, Requested: {issue_request.quantity_to_issue}"
        )
    
    # Get material instance
    instance = db.query(MaterialInstance).filter(
        MaterialInstance.id == allocation.material_instance_id
    ).first()
    
    # Update allocation
    allocation.quantity_issued = float(allocation.quantity_issued) + issue_request.quantity_to_issue
    allocation.issued_date = date.today()
    allocation.issued_by_id = current_user.id
    
    if allocation.quantity_issued >= allocation.quantity_allocated:
        allocation.is_fulfilled = True
    
    # Update material instance
    instance.reserved_quantity = max(0, float(instance.reserved_quantity) - issue_request.quantity_to_issue)
    instance.issued_quantity = float(instance.issued_quantity) + issue_request.quantity_to_issue
    
    # Update status
    old_status = instance.lifecycle_status
    instance.lifecycle_status = MaterialLifecycleStatus.ISSUED
    
    record_status_change(
        db, instance, old_status, MaterialLifecycleStatus.ISSUED, current_user,
        reference_type="ISSUE",
        reference_number=allocation.allocation_number,
        notes=f"Issued qty: {issue_request.quantity_to_issue}. {issue_request.notes or ''}"
    )
    
    # Update PO line item stage if linked
    if instance.po_line_item_id:
        po_line = db.query(POLineItem).filter(POLineItem.id == instance.po_line_item_id).first()
        if po_line:
            po_line.material_stage = MaterialStage.WIP
    
    db.commit()
    db.refresh(allocation)
    return allocation


@router.post("/allocations/{allocation_id}/return", response_model=MaterialAllocationResponse)
def return_issued_material(
    allocation_id: int,
    return_request: MaterialReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Return issued material back to storage."""
    allocation = db.query(MaterialAllocation).filter(
        MaterialAllocation.id == allocation_id
    ).first()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found"
        )
    
    # Check issued quantity
    if return_request.quantity_to_return > float(allocation.quantity_issued) - float(allocation.quantity_returned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Return quantity exceeds issued quantity"
        )
    
    # Get material instance
    instance = db.query(MaterialInstance).filter(
        MaterialInstance.id == allocation.material_instance_id
    ).first()
    
    # Update allocation
    allocation.quantity_returned = float(allocation.quantity_returned) + return_request.quantity_to_return
    allocation.is_fulfilled = False
    
    # Update material instance
    instance.issued_quantity = max(0, float(instance.issued_quantity) - return_request.quantity_to_return)
    
    # Update status back to IN_STORAGE if no more issued
    if instance.issued_quantity <= 0:
        old_status = instance.lifecycle_status
        instance.lifecycle_status = MaterialLifecycleStatus.IN_STORAGE
        
        record_status_change(
            db, instance, old_status, MaterialLifecycleStatus.IN_STORAGE, current_user,
            reference_type="RETURN",
            reference_number=allocation.allocation_number,
            reason=return_request.reason,
            notes=f"Returned qty: {return_request.quantity_to_return}. {return_request.notes or ''}"
        )
    
    db.commit()
    db.refresh(allocation)
    return allocation


@router.delete("/allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Cancel an allocation and release reserved quantity."""
    allocation = db.query(MaterialAllocation).filter(
        MaterialAllocation.id == allocation_id
    ).first()
    
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation not found"
        )
    
    if allocation.quantity_issued > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel allocation with issued quantity. Return issued material first."
        )
    
    # Get material instance and release reserved quantity
    instance = db.query(MaterialInstance).filter(
        MaterialInstance.id == allocation.material_instance_id
    ).first()
    
    instance.reserved_quantity = max(0, float(instance.reserved_quantity) - float(allocation.quantity_allocated))
    
    # Update status if no more reserved
    if instance.reserved_quantity <= 0 and instance.lifecycle_status == MaterialLifecycleStatus.RESERVED:
        old_status = instance.lifecycle_status
        instance.lifecycle_status = MaterialLifecycleStatus.IN_STORAGE
        
        record_status_change(
            db, instance, old_status, MaterialLifecycleStatus.IN_STORAGE, current_user,
            reference_type="CANCEL_ALLOCATION",
            reference_number=allocation.allocation_number,
            notes="Allocation cancelled, material released"
        )
    
    allocation.is_active = False
    
    db.commit()


# =============================================================================
# BOM Source Tracking Endpoints
# =============================================================================

@router.post("/bom-sources", response_model=BOMSourceTrackingResponse, status_code=status.HTTP_201_CREATED)
def create_bom_source_tracking(
    source_in: BOMSourceTrackingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Create BOM source tracking record linking BOM item to PO."""
    # Validate BOM and BOM item
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == source_in.bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BOM not found"
        )
    
    bom_item = db.query(BOMItem).filter(BOMItem.id == source_in.bom_item_id).first()
    if not bom_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BOM item not found"
        )
    
    source = BOMSourceTracking(**source_in.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/bom-sources", response_model=List[BOMSourceTrackingResponse])
def list_bom_sources(
    bom_id: Optional[int] = Query(None),
    purchase_order_id: Optional[int] = Query(None),
    unfulfilled_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List BOM source tracking records."""
    query = db.query(BOMSourceTracking)
    
    if bom_id:
        query = query.filter(BOMSourceTracking.bom_id == bom_id)
    if purchase_order_id:
        query = query.filter(BOMSourceTracking.purchase_order_id == purchase_order_id)
    if unfulfilled_only:
        query = query.filter(BOMSourceTracking.is_fulfilled == False)
    
    return query.all()


@router.put("/bom-sources/{source_id}", response_model=BOMSourceTrackingResponse)
def update_bom_source_tracking(
    source_id: int,
    source_in: BOMSourceTrackingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Update BOM source tracking record."""
    source = db.query(BOMSourceTracking).filter(BOMSourceTracking.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM source tracking not found"
        )
    
    update_data = source_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    
    # Auto-update dates
    if source_in.quantity_allocated and source_in.quantity_allocated > 0:
        source.allocated_date = date.today()
    if source_in.quantity_consumed and source_in.quantity_consumed > 0:
        source.consumed_date = date.today()
    
    # Check if fulfilled
    if float(source.quantity_consumed) >= float(source.quantity_required):
        source.is_fulfilled = True
    
    db.commit()
    db.refresh(source)
    return source


# =============================================================================
# Summary and Report Endpoints
# =============================================================================

@router.get("/summary/by-status", response_model=List[MaterialInventorySummary])
def get_inventory_summary_by_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get inventory summary grouped by lifecycle status."""
    results = db.query(
        MaterialInstance.lifecycle_status,
        func.count(MaterialInstance.id).label('count'),
        func.sum(MaterialInstance.quantity).label('total_quantity'),
        func.sum(MaterialInstance.quantity * func.coalesce(MaterialInstance.unit_cost, 0)).label('total_value')
    ).group_by(MaterialInstance.lifecycle_status).all()
    
    return [
        MaterialInventorySummary(
            status=SchemaLifecycleStatus(r.lifecycle_status.value),
            count=r.count,
            total_quantity=float(r.total_quantity or 0),
            total_value=float(r.total_value or 0)
        )
        for r in results
    ]


@router.get("/summary/project/{project_id}", response_model=ProjectMaterialSummary)
def get_project_material_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get material requirements summary for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    allocations = db.query(MaterialAllocation).filter(
        MaterialAllocation.project_id == project_id
    ).all()
    
    total_required = len(allocations)
    total_allocated = len([a for a in allocations if a.is_active])
    total_issued = len([a for a in allocations if a.quantity_issued > 0])
    pending = len([a for a in allocations if a.is_active and not a.is_fulfilled])
    
    allocation_pct = (total_allocated / total_required * 100) if total_required > 0 else 0
    
    return ProjectMaterialSummary(
        project_id=project.id,
        project_name=project.name,
        total_materials_required=total_required,
        total_materials_allocated=total_allocated,
        total_materials_issued=total_issued,
        materials_pending=pending,
        allocation_percentage=round(allocation_pct, 2),
        materials=[MaterialAllocationResponse.model_validate(a) for a in allocations]
    )


@router.get("/by-po/{po_id}", response_model=List[MaterialInstanceResponse])
def get_materials_by_po(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get all material instances linked to a specific Purchase Order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    instances = db.query(MaterialInstance).filter(
        MaterialInstance.purchase_order_id == po_id
    ).order_by(MaterialInstance.item_number).all()
    
    return instances


@router.get("/lifecycle-report/{instance_id}", response_model=MaterialLifecycleReport)
def get_material_lifecycle_report(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get comprehensive lifecycle report for a material instance."""
    instance = db.query(MaterialInstance).options(
        joinedload(MaterialInstance.supplier),
        joinedload(MaterialInstance.purchase_order)
    ).filter(MaterialInstance.id == instance_id).first()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material instance not found"
        )
    
    history = db.query(MaterialStatusHistory).options(
        joinedload(MaterialStatusHistory.changed_by)
    ).filter(
        MaterialStatusHistory.material_instance_id == instance_id
    ).order_by(MaterialStatusHistory.created_at.desc()).all()
    
    # Calculate days in current status
    if history:
        last_change = history[0].created_at
        days_in_status = (datetime.utcnow() - last_change).days
    else:
        days_in_status = (datetime.utcnow() - instance.created_at).days
    
    history_items = []
    for h in history:
        item = MaterialStatusHistoryResponse.model_validate(h)
        if h.changed_by:
            item.changed_by_name = h.changed_by.full_name
        history_items.append(item)
    
    return MaterialLifecycleReport(
        material_instance_id=instance.id,
        item_number=instance.item_number,
        title=instance.title,
        current_status=SchemaLifecycleStatus(instance.lifecycle_status.value),
        po_number=instance.purchase_order.po_number if instance.purchase_order else None,
        supplier_name=instance.supplier.name if instance.supplier else None,
        order_date=instance.order_date,
        received_date=instance.received_date,
        days_in_current_status=days_in_status,
        status_history=history_items
    )
