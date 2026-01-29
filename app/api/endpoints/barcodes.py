"""
Barcode management endpoints with PO integration.

Provides:
- Barcode generation with PO reference
- QR code generation for mobile scanning  
- Scan-to-receive against PO
- WIP tracking with raw material traceability
- Finished goods barcode with full traceability
- Barcode validation against PO details
"""
import base64
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from io import BytesIO

from app.db.session import get_db
from app.models.user import User
from app.models.material import Material
from app.models.supplier import Supplier
from app.models.barcode import (
    BarcodeLabel, BarcodeScanLog, BarcodeTemplate,
    BarcodeType, BarcodeStatus, BarcodeEntityType, TraceabilityStage
)
from app.models.purchase_order import PurchaseOrder, POLineItem, GoodsReceiptNote, GRNLineItem
from app.models.material_instance import MaterialInstance
from app.schemas.barcode import (
    BarcodeLabelCreate, BarcodeLabelUpdate, BarcodeLabelResponse, BarcodeLabelDetailResponse,
    BarcodeLabelFromPO, BarcodeScanRequest, BarcodeScanByQRRequest, ScanToReceiveRequest,
    BarcodeScanLogResponse, BarcodeValidationRequest, BarcodeValidationResult,
    GenerateBarcodeRequest, GenerateBarcodeResponse, BulkGenerateBarcodeRequest, BulkGenerateBarcodeResponse,
    CreateWIPBarcodeRequest, CreateFinishedGoodsBarcodeRequest,
    BarcodeTemplateCreate, BarcodeTemplateUpdate, BarcodeTemplateResponse,
    TraceabilityChainItem, TraceabilityChainResponse, BarcodeSearchRequest,
    BarcodeSummaryByStage, BarcodeSummaryByPO,
    BarcodeType as SchemaBarcodeType, BarcodeStatus as SchemaBarcodeStatus,
    BarcodeEntityType as SchemaEntityType, TraceabilityStage as SchemaTraceabilityStage
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import (
    get_current_user, require_store, require_qa, require_engineer,
    require_any_role, PaginationParams
)
from app.core.barcode_utils import (
    BarcodeGenerator, BarcodeValidator,
    generate_po_receipt_barcode, generate_wip_barcode, generate_finished_goods_barcode
)


router = APIRouter(prefix="/barcodes", tags=["Barcodes"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_next_sequence(db: Session, prefix: str) -> int:
    """Get next sequence number for barcode generation."""
    last_barcode = db.query(BarcodeLabel).filter(
        BarcodeLabel.barcode_value.like(f"{prefix}%")
    ).order_by(BarcodeLabel.id.desc()).first()
    
    if last_barcode:
        # Extract sequence from barcode
        try:
            parts = last_barcode.barcode_value.split("-")
            return int(parts[-1]) + 1
        except (ValueError, IndexError):
            pass
    return 1


def record_scan(
    db: Session,
    barcode: BarcodeLabel,
    user: User,
    action: str,
    request: Request,
    quantity: Optional[float] = None,
    location_from: Optional[str] = None,
    location_to: Optional[str] = None,
    po_id: Optional[int] = None,
    grn_id: Optional[int] = None,
    is_successful: bool = True,
    error_message: Optional[str] = None,
    validation_result: Optional[dict] = None,
    reference_type: Optional[str] = None,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None
) -> BarcodeScanLog:
    """Record a barcode scan in the log."""
    scan_log = BarcodeScanLog(
        barcode_label_id=barcode.id,
        scanned_by=user.id,
        scan_action=action,
        scan_location=location_to or location_from,
        scan_device=request.headers.get("User-Agent", "")[:100] if request else None,
        purchase_order_id=po_id,
        grn_id=grn_id,
        quantity_scanned=quantity,
        quantity_before=barcode.current_quantity,
        status_before=barcode.status.value if barcode.status else None,
        stage_before=barcode.traceability_stage.value if barcode.traceability_stage else None,
        location_from=location_from,
        location_to=location_to,
        is_successful=is_successful,
        error_message=error_message,
        validation_result=validation_result,
        reference_type=reference_type,
        reference_number=reference_number,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:255] if request else None,
        notes=notes
    )
    db.add(scan_log)
    
    # Update barcode scan tracking
    barcode.scan_count += 1
    barcode.last_scanned_at = datetime.utcnow()
    barcode.last_scanned_by = user.id
    barcode.last_scan_location = location_to or location_from
    barcode.last_scan_action = action
    
    return scan_log


# =============================================================================
# Barcode CRUD Endpoints
# =============================================================================

@router.get("", response_model=PaginatedResponse[BarcodeLabelResponse])
def list_barcodes(
    pagination: PaginationParams = Depends(),
    entity_type: Optional[SchemaEntityType] = Query(None),
    status: Optional[SchemaBarcodeStatus] = Query(None),
    traceability_stage: Optional[SchemaTraceabilityStage] = Query(None),
    po_number: Optional[str] = Query(None),
    material_id: Optional[int] = Query(None),
    lot_number: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search barcode value, lot, serial, heat number"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """List barcodes with filtering options."""
    query = db.query(BarcodeLabel)
    
    if entity_type:
        query = query.filter(BarcodeLabel.entity_type == entity_type.value)
    if status:
        query = query.filter(BarcodeLabel.status == status.value)
    if traceability_stage:
        query = query.filter(BarcodeLabel.traceability_stage == traceability_stage.value)
    if po_number:
        query = query.filter(BarcodeLabel.po_number == po_number)
    if material_id:
        query = query.filter(BarcodeLabel.material_id == material_id)
    if lot_number:
        query = query.filter(BarcodeLabel.lot_number.ilike(f"%{lot_number}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                BarcodeLabel.barcode_value.ilike(search_term),
                BarcodeLabel.lot_number.ilike(search_term),
                BarcodeLabel.serial_number.ilike(search_term),
                BarcodeLabel.heat_number.ilike(search_term)
            )
        )
    
    total = query.count()
    barcodes = query.order_by(BarcodeLabel.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=barcodes,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


@router.get("/{barcode_id}", response_model=BarcodeLabelDetailResponse)
def get_barcode(
    barcode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get barcode details by ID."""
    barcode = db.query(BarcodeLabel).options(
        joinedload(BarcodeLabel.purchase_order),
        joinedload(BarcodeLabel.material),
        joinedload(BarcodeLabel.supplier),
        joinedload(BarcodeLabel.parent_barcode)
    ).filter(BarcodeLabel.id == barcode_id).first()
    
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    # Build response with additional details
    response = BarcodeLabelDetailResponse.model_validate(barcode)
    
    if barcode.purchase_order:
        response.po_status = barcode.purchase_order.status.value if barcode.purchase_order.status else None
    if barcode.material:
        response.material_type = barcode.material.material_type.value if barcode.material.material_type else None
    if barcode.parent_barcode:
        response.parent_barcode_value = barcode.parent_barcode.barcode_value
    
    # Count child barcodes
    response.child_barcode_count = db.query(BarcodeLabel).filter(
        BarcodeLabel.parent_barcode_id == barcode_id
    ).count()
    
    return response


@router.get("/lookup/{barcode_value}", response_model=BarcodeLabelDetailResponse)
def lookup_barcode(
    barcode_value: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Look up barcode by value."""
    barcode = db.query(BarcodeLabel).options(
        joinedload(BarcodeLabel.purchase_order),
        joinedload(BarcodeLabel.material),
        joinedload(BarcodeLabel.supplier)
    ).filter(BarcodeLabel.barcode_value == barcode_value).first()
    
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    return barcode


@router.post("", response_model=BarcodeLabelResponse, status_code=status.HTTP_201_CREATED)
def create_barcode(
    barcode_in: BarcodeLabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Create a new barcode label."""
    # Generate barcode value if not provided
    if barcode_in.auto_generate or not barcode_in.barcode_value:
        sequence = get_next_sequence(db, BarcodeGenerator.PREFIXES.get(barcode_in.entity_type.value, "BC"))
        barcode_value = BarcodeGenerator.generate_barcode_value(
            entity_type=barcode_in.entity_type.value,
            po_number=barcode_in.po_number,
            material_id=barcode_in.material_id,
            lot_number=barcode_in.lot_number,
            sequence=sequence
        )
    else:
        barcode_value = barcode_in.barcode_value
    
    # Check uniqueness
    existing = db.query(BarcodeLabel).filter(BarcodeLabel.barcode_value == barcode_value).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Barcode value already exists"
        )
    
    # Generate QR data
    qr_data = BarcodeGenerator.generate_qr_data(
        barcode_value=barcode_value,
        po_number=barcode_in.po_number,
        material_part_number=barcode_in.material_part_number,
        material_name=barcode_in.material_name,
        specification=barcode_in.specification,
        lot_number=barcode_in.lot_number,
        batch_number=barcode_in.batch_number,
        heat_number=barcode_in.heat_number,
        quantity=barcode_in.initial_quantity,
        unit_of_measure=barcode_in.unit_of_measure,
        supplier_name=barcode_in.supplier_name,
        manufacture_date=barcode_in.manufacture_date,
        expiry_date=barcode_in.expiry_date,
        traceability_stage=barcode_in.traceability_stage.value
    )
    
    barcode_data = barcode_in.model_dump(exclude={'auto_generate', 'barcode_value'})
    barcode_data['barcode_value'] = barcode_value
    barcode_data['qr_data'] = qr_data
    barcode_data['status'] = BarcodeStatus.ACTIVE
    # Ensure enum fields use model enums (schema may dump as strings)
    barcode_data['entity_type'] = BarcodeEntityType(barcode_data['entity_type'].value if hasattr(barcode_data['entity_type'], 'value') else barcode_data['entity_type'])
    barcode_data['traceability_stage'] = TraceabilityStage(barcode_data['traceability_stage'].value if hasattr(barcode_data['traceability_stage'], 'value') else barcode_data['traceability_stage'])
    barcode_data['barcode_type'] = BarcodeType(barcode_data['barcode_type'].value if hasattr(barcode_data['barcode_type'], 'value') else barcode_data['barcode_type'])
    
    barcode = BarcodeLabel(**barcode_data)
    db.add(barcode)
    db.commit()
    db.refresh(barcode)
    return barcode


@router.put("/{barcode_id}", response_model=BarcodeLabelResponse)
def update_barcode(
    barcode_id: int,
    barcode_in: BarcodeLabelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Update barcode details."""
    barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    update_data = barcode_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barcode, field, value)
    
    db.commit()
    db.refresh(barcode)
    return barcode


@router.delete("/{barcode_id}", status_code=status.HTTP_204_NO_CONTENT)
def void_barcode(
    barcode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_engineer)
):
    """Void a barcode (soft delete)."""
    barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    barcode.status = BarcodeStatus.VOID
    db.commit()


# =============================================================================
# Barcode Generation Endpoints
# =============================================================================

@router.post("/generate", response_model=GenerateBarcodeResponse)
def generate_barcode(
    request_data: GenerateBarcodeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Generate a new barcode with optional QR code and images."""
    sequence = get_next_sequence(db, BarcodeGenerator.PREFIXES.get(request_data.entity_type.value, "BC"))
    
    barcode_value = BarcodeGenerator.generate_barcode_value(
        entity_type=request_data.entity_type.value,
        po_number=request_data.po_number,
        material_id=request_data.material_id,
        lot_number=request_data.lot_number,
        sequence=sequence
    )
    
    # Generate QR data
    qr_data = BarcodeGenerator.generate_qr_data(
        barcode_value=barcode_value,
        po_number=request_data.po_number,
        material_part_number=request_data.material_part_number,
        material_name=request_data.material_name,
        specification=request_data.specification,
        lot_number=request_data.lot_number,
        batch_number=request_data.batch_number,
        heat_number=request_data.heat_number,
        quantity=request_data.quantity,
        unit_of_measure=request_data.unit_of_measure,
        supplier_name=request_data.supplier_name,
        manufacture_date=request_data.manufacture_date,
        expiry_date=request_data.expiry_date,
        traceability_stage="received"
    )
    
    # Create barcode record
    barcode = BarcodeLabel(
        barcode_value=barcode_value,
        barcode_type=BarcodeType(request_data.barcode_type.value),
        status=BarcodeStatus.ACTIVE,
        entity_type=BarcodeEntityType(request_data.entity_type.value),
        entity_id=request_data.entity_id,
        traceability_stage=TraceabilityStage.RECEIVED,
        po_number=request_data.po_number,
        po_line_item_id=request_data.po_line_item_id,
        material_id=request_data.material_id,
        material_part_number=request_data.material_part_number,
        material_name=request_data.material_name,
        specification=request_data.specification,
        lot_number=request_data.lot_number,
        batch_number=request_data.batch_number,
        serial_number=request_data.serial_number,
        heat_number=request_data.heat_number,
        initial_quantity=request_data.quantity,
        current_quantity=request_data.quantity,
        unit_of_measure=request_data.unit_of_measure,
        supplier_name=request_data.supplier_name,
        manufacture_date=request_data.manufacture_date,
        expiry_date=request_data.expiry_date,
        current_location=request_data.storage_location,
        bin_number=request_data.bin_number,
        work_order_reference=request_data.work_order_reference,
        parent_barcode_id=request_data.parent_barcode_id,
        qr_data=qr_data
    )
    
    db.add(barcode)
    db.commit()
    db.refresh(barcode)
    
    # Generate images
    images = BarcodeGenerator.generate_material_barcode_with_qr(barcode_value, qr_data)
    
    response = GenerateBarcodeResponse(
        barcode_id=barcode.id,
        barcode_value=barcode_value,
        barcode_type=SchemaBarcodeType(request_data.barcode_type.value),
        qr_data=qr_data,
        qr_data_encoded=images.get('qr_data_encoded')
    )
    
    # Encode images to base64 if available
    if images.get('barcode'):
        response.barcode_image_base64 = base64.b64encode(images['barcode']).decode()
    if images.get('qr_code'):
        response.qr_image_base64 = base64.b64encode(images['qr_code']).decode()
    
    return response


@router.post("/generate-from-po", response_model=GenerateBarcodeResponse)
def generate_barcode_from_po(
    request_data: BarcodeLabelFromPO,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Generate barcode from PO line item with all PO details embedded."""
    # Get PO line item with related data
    po_line = db.query(POLineItem).options(
        joinedload(POLineItem.purchase_order).joinedload(PurchaseOrder.supplier),
        joinedload(POLineItem.material)
    ).filter(POLineItem.id == request_data.po_line_item_id).first()
    
    if not po_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PO line item not found"
        )
    
    po = po_line.purchase_order
    material = po_line.material
    supplier = po.supplier
    
    # Get GRN line item if provided
    grn_line = None
    if request_data.grn_line_item_id:
        grn_line = db.query(GRNLineItem).filter(
            GRNLineItem.id == request_data.grn_line_item_id
        ).first()
    
    # Generate barcode
    sequence = get_next_sequence(db, "RM")
    
    barcode_result = generate_po_receipt_barcode(
        po_number=po.po_number,
        po_line_item_id=po_line.id,
        material_id=material.id if material else 0,
        material_part_number=material.item_number if material else "",
        material_name=material.title if material else "",
        specification=po_line.specification or (material.specification if material else None),
        lot_number=request_data.lot_number or (grn_line.lot_number if grn_line else None),
        batch_number=request_data.batch_number or (grn_line.batch_number if grn_line else None),
        heat_number=request_data.heat_number or (grn_line.heat_number if grn_line else None),
        quantity=request_data.quantity or float(po_line.quantity_ordered),
        unit_of_measure=po_line.unit_of_measure,
        supplier_name=supplier.name if supplier else None,
        manufacture_date=request_data.manufacture_date or (grn_line.manufacture_date if grn_line else None),
        expiry_date=request_data.expiry_date or (grn_line.expiry_date if grn_line else None),
        sequence=sequence
    )
    
    # Create barcode record
    barcode = BarcodeLabel(
        barcode_value=barcode_result['barcode_value'],
        barcode_type=BarcodeType(request_data.barcode_type.value),
        status=BarcodeStatus.ACTIVE,
        entity_type=BarcodeEntityType.RAW_MATERIAL,
        entity_id=po_line.id,
        traceability_stage=TraceabilityStage.RECEIVED,
        purchase_order_id=po.id,
        po_line_item_id=po_line.id,
        grn_id=grn_line.goods_receipt_id if grn_line else None,
        po_number=po.po_number,
        grn_number=None,  # Will be set if GRN exists
        material_id=material.id if material else None,
        material_part_number=material.item_number if material else None,
        material_name=material.title if material else None,
        specification=po_line.specification,
        supplier_id=supplier.id if supplier else None,
        supplier_name=supplier.name if supplier else None,
        lot_number=request_data.lot_number or (grn_line.lot_number if grn_line else None),
        batch_number=request_data.batch_number or (grn_line.batch_number if grn_line else None),
        heat_number=request_data.heat_number or (grn_line.heat_number if grn_line else None),
        initial_quantity=request_data.quantity or float(po_line.quantity_ordered),
        current_quantity=request_data.quantity or float(po_line.quantity_ordered),
        unit_of_measure=po_line.unit_of_measure,
        manufacture_date=request_data.manufacture_date,
        expiry_date=request_data.expiry_date,
        received_date=date.today(),
        current_location=request_data.storage_location,
        bin_number=request_data.bin_number,
        qr_data=barcode_result['qr_data'],
        notes=request_data.notes
    )
    
    db.add(barcode)
    db.commit()
    db.refresh(barcode)
    
    response = GenerateBarcodeResponse(
        barcode_id=barcode.id,
        barcode_value=barcode_result['barcode_value'],
        barcode_type=request_data.barcode_type,
        qr_data=barcode_result['qr_data'],
        qr_data_encoded=barcode_result.get('qr_data_encoded')
    )
    
    if barcode_result.get('barcode_image'):
        response.barcode_image_base64 = base64.b64encode(barcode_result['barcode_image']).decode()
    if barcode_result.get('qr_image'):
        response.qr_image_base64 = base64.b64encode(barcode_result['qr_image']).decode()
    
    return response


# =============================================================================
# Scan Endpoints
# =============================================================================

@router.post("/scan", response_model=BarcodeScanLogResponse)
def scan_barcode(
    scan_request: BarcodeScanRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """
    Process a barcode scan.
    
    Supported actions:
    - po_receipt: Receive against PO
    - inspection: QC inspection scan
    - issue: Issue to production
    - wip_start: Start WIP processing
    - wip_complete: Complete WIP stage
    - transfer: Transfer location
    - inventory: Inventory count
    """
    barcode = db.query(BarcodeLabel).filter(
        BarcodeLabel.barcode_value == scan_request.barcode_value
    ).first()
    
    if not barcode:
        # Record failed scan attempt
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barcode not found"
        )
    
    # Validate barcode status
    if barcode.status == BarcodeStatus.VOID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Barcode has been voided"
        )
    
    if barcode.status == BarcodeStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Barcode has expired"
        )
    
    # Process based on action
    old_status = barcode.status
    old_stage = barcode.traceability_stage
    old_location = barcode.current_location
    
    if scan_request.scan_action == "po_receipt":
        # Validate PO if provided
        if scan_request.purchase_order_id and barcode.purchase_order_id != scan_request.purchase_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Barcode PO mismatch. Expected PO ID: {scan_request.purchase_order_id}"
            )
        barcode.traceability_stage = TraceabilityStage.RECEIVED
        barcode.received_date = date.today()
        
    elif scan_request.scan_action == "inspection":
        barcode.traceability_stage = TraceabilityStage.INSPECTED
        
    elif scan_request.scan_action == "issue":
        barcode.traceability_stage = TraceabilityStage.IN_PRODUCTION
        if scan_request.quantity:
            barcode.current_quantity = max(0, (barcode.current_quantity or 0) - scan_request.quantity)
            if barcode.current_quantity <= 0:
                barcode.status = BarcodeStatus.CONSUMED
        
    elif scan_request.scan_action == "wip_start":
        barcode.traceability_stage = TraceabilityStage.IN_PRODUCTION
        barcode.work_order_reference = scan_request.reference_number
        
    elif scan_request.scan_action == "wip_complete":
        barcode.traceability_stage = TraceabilityStage.COMPLETED
        
    elif scan_request.scan_action == "transfer":
        if scan_request.new_location:
            barcode.current_location = scan_request.new_location
        if scan_request.new_bin:
            barcode.bin_number = scan_request.new_bin
    
    # Update location if provided
    if scan_request.new_location:
        barcode.current_location = scan_request.new_location
    if scan_request.new_bin:
        barcode.bin_number = scan_request.new_bin
    
    # Record scan
    scan_log = record_scan(
        db=db,
        barcode=barcode,
        user=current_user,
        action=scan_request.scan_action,
        request=request,
        quantity=scan_request.quantity,
        location_from=old_location,
        location_to=scan_request.new_location,
        po_id=scan_request.purchase_order_id,
        grn_id=scan_request.grn_id,
        reference_type=scan_request.reference_type,
        reference_number=scan_request.reference_number,
        notes=scan_request.notes
    )
    
    # Update scan log with after values
    scan_log.quantity_after = barcode.current_quantity
    scan_log.status_after = barcode.status.value
    scan_log.stage_after = barcode.traceability_stage.value
    
    db.commit()
    db.refresh(scan_log)
    
    return scan_log


@router.post("/scan-to-receive", response_model=BarcodeScanLogResponse)
def scan_to_receive(
    receive_request: ScanToReceiveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """
    Scan-to-receive against PO with validation.
    
    Validates:
    - Barcode matches PO
    - Material matches PO line
    - Quantity is valid
    - Material not expired
    """
    # Get barcode
    barcode = db.query(BarcodeLabel).filter(
        BarcodeLabel.barcode_value == receive_request.barcode_value
    ).first()
    
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    # Get PO and line item
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == receive_request.purchase_order_id).first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Order not found")
    
    po_line = db.query(POLineItem).filter(POLineItem.id == receive_request.po_line_item_id).first()
    if not po_line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO Line Item not found")
    
    # Validation
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'checks': {}
    }
    
    # Check PO match
    if receive_request.validate_po:
        if barcode.po_number and barcode.po_number != po.po_number:
            validation_result['errors'].append(f"PO mismatch: barcode={barcode.po_number}, expected={po.po_number}")
            validation_result['is_valid'] = False
        validation_result['checks']['po_match'] = not validation_result['errors']
        
        # Check quantity
        outstanding = float(po_line.quantity_ordered) - float(po_line.quantity_received)
        if receive_request.quantity_received > outstanding:
            validation_result['warnings'].append(f"Quantity {receive_request.quantity_received} exceeds outstanding {outstanding}")
        validation_result['checks']['quantity_valid'] = receive_request.quantity_received <= outstanding
        
        # Check expiry
        if barcode.expiry_date and barcode.expiry_date < date.today():
            validation_result['errors'].append("Material has expired")
            validation_result['is_valid'] = False
        validation_result['checks']['not_expired'] = not (barcode.expiry_date and barcode.expiry_date < date.today())
    
    if not validation_result['is_valid']:
        # Record failed scan
        scan_log = record_scan(
            db=db,
            barcode=barcode,
            user=current_user,
            action="po_receipt",
            request=request,
            quantity=receive_request.quantity_received,
            location_to=receive_request.storage_location,
            po_id=po.id,
            is_successful=False,
            error_message="; ".join(validation_result['errors']),
            validation_result=validation_result,
            reference_type="PO",
            reference_number=po.po_number,
            notes=receive_request.notes
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Validation failed",
                "errors": validation_result['errors'],
                "warnings": validation_result['warnings']
            }
        )
    
    # Process receipt
    old_location = barcode.current_location
    barcode.traceability_stage = TraceabilityStage.RECEIVED
    barcode.received_date = date.today()
    barcode.current_location = receive_request.storage_location
    barcode.bin_number = receive_request.bin_number
    barcode.purchase_order_id = po.id
    barcode.po_line_item_id = po_line.id
    barcode.grn_id = receive_request.grn_id
    barcode.po_number = po.po_number
    
    # Update PO line received quantity
    po_line.quantity_received = float(po_line.quantity_received) + receive_request.quantity_received
    
    # Record successful scan
    scan_log = record_scan(
        db=db,
        barcode=barcode,
        user=current_user,
        action="po_receipt",
        request=request,
        quantity=receive_request.quantity_received,
        location_from=old_location,
        location_to=receive_request.storage_location,
        po_id=po.id,
        grn_id=receive_request.grn_id,
        is_successful=True,
        validation_result=validation_result,
        reference_type="PO",
        reference_number=po.po_number,
        notes=receive_request.notes
    )
    
    scan_log.quantity_after = barcode.current_quantity
    scan_log.status_after = barcode.status.value
    scan_log.stage_after = barcode.traceability_stage.value
    
    db.commit()
    db.refresh(scan_log)
    
    return scan_log


@router.post("/validate", response_model=BarcodeValidationResult)
def validate_barcode(
    validation_request: BarcodeValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Validate barcode against PO and material details."""
    barcode = db.query(BarcodeLabel).filter(
        BarcodeLabel.barcode_value == validation_request.barcode_value
    ).first()
    
    result = BarcodeValidationResult(
        is_valid=False,
        barcode_found=barcode is not None,
        barcode_active=False
    )
    
    if not barcode:
        result.errors.append("Barcode not found")
        return result
    
    result.barcode_id = barcode.id
    result.barcode_status = barcode.status.value
    result.barcode_active = barcode.status == BarcodeStatus.ACTIVE
    result.po_number = barcode.po_number
    result.material_part_number = barcode.material_part_number
    result.current_quantity = barcode.current_quantity
    
    if not result.barcode_active:
        result.errors.append(f"Barcode is {barcode.status.value}")
        return result
    
    # Check PO match
    if validation_request.purchase_order_id:
        result.po_match = barcode.purchase_order_id == validation_request.purchase_order_id
        if not result.po_match:
            result.errors.append("PO does not match")
        result.checks['po_match'] = result.po_match
    
    # Check material match
    if validation_request.expected_material_id:
        result.material_match = barcode.material_id == validation_request.expected_material_id
        if not result.material_match:
            result.errors.append("Material does not match")
        result.checks['material_match'] = result.material_match
    
    # Check quantity
    if validation_request.expected_quantity:
        result.quantity_valid = (barcode.current_quantity or 0) >= validation_request.expected_quantity
        if not result.quantity_valid:
            result.warnings.append(f"Insufficient quantity: {barcode.current_quantity} < {validation_request.expected_quantity}")
        result.checks['quantity_valid'] = result.quantity_valid
    
    # Check expiry
    if barcode.expiry_date:
        result.not_expired = barcode.expiry_date >= date.today()
        if not result.not_expired:
            result.errors.append("Material has expired")
        result.checks['not_expired'] = result.not_expired
    else:
        result.not_expired = True
        result.checks['not_expired'] = True
    
    # Overall validity
    result.is_valid = len(result.errors) == 0
    
    return result


# =============================================================================
# WIP and Finished Goods Barcode Endpoints
# =============================================================================

@router.post("/create-wip", response_model=GenerateBarcodeResponse)
def create_wip_barcode(
    wip_request: CreateWIPBarcodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Create WIP barcode linked to raw material barcode for traceability."""
    parent_barcode = db.query(BarcodeLabel).filter(
        BarcodeLabel.id == wip_request.parent_barcode_id
    ).first()
    
    if not parent_barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent barcode not found")
    
    if parent_barcode.status != BarcodeStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent barcode is not active")
    
    # Check available quantity
    available = parent_barcode.current_quantity or 0
    if wip_request.quantity_used > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient quantity. Available: {available}, Requested: {wip_request.quantity_used}"
        )
    
    # Generate WIP barcode
    sequence = get_next_sequence(db, "WIP")
    wip_result = generate_wip_barcode(
        parent_barcode=parent_barcode.barcode_value,
        work_order_reference=wip_request.work_order_reference,
        quantity_used=wip_request.quantity_used,
        unit_of_measure=wip_request.unit_of_measure,
        original_qr_data=parent_barcode.qr_data or {},
        sequence=sequence
    )
    
    # Create WIP barcode record
    wip_barcode = BarcodeLabel(
        barcode_value=wip_result['barcode_value'],
        barcode_type=BarcodeType.QR_CODE,
        status=BarcodeStatus.ACTIVE,
        entity_type=BarcodeEntityType.WIP,
        entity_id=parent_barcode.entity_id,
        traceability_stage=TraceabilityStage.IN_PRODUCTION,
        purchase_order_id=parent_barcode.purchase_order_id,
        po_line_item_id=parent_barcode.po_line_item_id,
        po_number=parent_barcode.po_number,
        material_id=parent_barcode.material_id,
        material_part_number=parent_barcode.material_part_number,
        material_name=parent_barcode.material_name,
        specification=parent_barcode.specification,
        supplier_id=parent_barcode.supplier_id,
        supplier_name=parent_barcode.supplier_name,
        lot_number=parent_barcode.lot_number,
        batch_number=parent_barcode.batch_number,
        heat_number=parent_barcode.heat_number,
        initial_quantity=wip_request.quantity_used,
        current_quantity=wip_request.quantity_used,
        unit_of_measure=wip_request.unit_of_measure,
        work_order_reference=wip_request.work_order_reference,
        parent_barcode_id=parent_barcode.id,
        qr_data=wip_result['qr_data'],
        notes=wip_request.notes
    )
    
    # Deduct from parent barcode
    parent_barcode.current_quantity = available - wip_request.quantity_used
    if parent_barcode.current_quantity <= 0:
        parent_barcode.status = BarcodeStatus.CONSUMED
    
    db.add(wip_barcode)
    db.commit()
    db.refresh(wip_barcode)
    
    response = GenerateBarcodeResponse(
        barcode_id=wip_barcode.id,
        barcode_value=wip_result['barcode_value'],
        barcode_type=SchemaBarcodeType.QR_CODE,
        qr_data=wip_result['qr_data']
    )
    
    if wip_result.get('barcode_image'):
        response.barcode_image_base64 = base64.b64encode(wip_result['barcode_image']).decode()
    if wip_result.get('qr_image'):
        response.qr_image_base64 = base64.b64encode(wip_result['qr_image']).decode()
    
    return response


@router.post("/create-finished-goods", response_model=GenerateBarcodeResponse)
def create_finished_goods_barcode(
    fg_request: CreateFinishedGoodsBarcodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store)
):
    """Create finished goods barcode with full traceability to source materials."""
    # Get parent barcodes
    parent_barcodes = db.query(BarcodeLabel).filter(
        BarcodeLabel.id.in_(fg_request.parent_barcode_ids)
    ).all()
    
    if len(parent_barcodes) != len(fg_request.parent_barcode_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some parent barcodes not found"
        )
    
    parent_values = [bc.barcode_value for bc in parent_barcodes]
    
    # Generate FG barcode
    sequence = get_next_sequence(db, "FG")
    fg_result = generate_finished_goods_barcode(
        parent_barcodes=parent_values,
        part_number=fg_request.part_number,
        part_name=fg_request.part_name,
        serial_number=fg_request.serial_number,
        work_order_reference=fg_request.work_order_reference,
        sequence=sequence
    )
    
    # Get PO info from first parent (for traceability)
    first_parent = parent_barcodes[0]
    
    # Create FG barcode record
    fg_barcode = BarcodeLabel(
        barcode_value=fg_result['barcode_value'],
        barcode_type=BarcodeType.QR_CODE,
        status=BarcodeStatus.ACTIVE,
        entity_type=BarcodeEntityType.FINISHED_GOODS,
        entity_id=0,  # Will be linked to part if available
        traceability_stage=TraceabilityStage.COMPLETED,
        purchase_order_id=first_parent.purchase_order_id,
        po_number=first_parent.po_number,
        material_part_number=fg_request.part_number,
        material_name=fg_request.part_name,
        serial_number=fg_request.serial_number,
        initial_quantity=1,
        current_quantity=1,
        unit_of_measure="ea",
        work_order_reference=fg_request.work_order_reference,
        project_reference=fg_request.project_reference,
        parent_barcode_id=first_parent.id,  # Link to first parent for chain
        qr_data=fg_result['qr_data'],
        notes=fg_request.notes
    )
    
    # Mark parent barcodes as consumed
    for parent in parent_barcodes:
        parent.status = BarcodeStatus.CONSUMED
        parent.traceability_stage = TraceabilityStage.CONSUMED
    
    db.add(fg_barcode)
    db.commit()
    db.refresh(fg_barcode)
    
    response = GenerateBarcodeResponse(
        barcode_id=fg_barcode.id,
        barcode_value=fg_result['barcode_value'],
        barcode_type=SchemaBarcodeType.QR_CODE,
        qr_data=fg_result['qr_data']
    )
    
    if fg_result.get('barcode_image'):
        response.barcode_image_base64 = base64.b64encode(fg_result['barcode_image']).decode()
    if fg_result.get('qr_image'):
        response.qr_image_base64 = base64.b64encode(fg_result['qr_image']).decode()
    
    return response


# =============================================================================
# Traceability Endpoints
# =============================================================================

@router.get("/{barcode_id}/traceability", response_model=TraceabilityChainResponse)
def get_traceability_chain(
    barcode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get full traceability chain for a barcode back to source PO."""
    barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    # Build chain
    chain = []
    current = barcode
    
    while current:
        chain_item = TraceabilityChainItem(
            barcode_id=current.id,
            barcode_value=current.barcode_value,
            entity_type=SchemaEntityType(current.entity_type.value),
            traceability_stage=SchemaTraceabilityStage(current.traceability_stage.value),
            po_number=current.po_number,
            material_part_number=current.material_part_number,
            lot_number=current.lot_number,
            quantity=current.current_quantity,
            created_at=current.created_at
        )
        chain.append(chain_item)
        
        if current.parent_barcode_id:
            current = db.query(BarcodeLabel).filter(
                BarcodeLabel.id == current.parent_barcode_id
            ).first()
        else:
            current = None
    
    # Get source info from last item in chain (original raw material)
    source_po = chain[-1].po_number if chain else None
    
    return TraceabilityChainResponse(
        barcode_id=barcode.id,
        barcode_value=barcode.barcode_value,
        chain_length=len(chain),
        chain=chain,
        source_po_number=source_po,
        finished_goods_serial=barcode.serial_number if barcode.entity_type == BarcodeEntityType.FINISHED_GOODS else None
    )


@router.get("/{barcode_id}/scan-history", response_model=List[BarcodeScanLogResponse])
def get_barcode_scan_history(
    barcode_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get scan history for a barcode."""
    barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    scans = db.query(BarcodeScanLog).options(
        joinedload(BarcodeScanLog.scanned_by_user)
    ).filter(
        BarcodeScanLog.barcode_label_id == barcode_id
    ).order_by(BarcodeScanLog.scan_timestamp.desc()).limit(limit).all()
    
    result = []
    for scan in scans:
        item = BarcodeScanLogResponse.model_validate(scan)
        if scan.scanned_by_user:
            item.scanned_by_name = scan.scanned_by_user.full_name
        result.append(item)
    
    return result


# =============================================================================
# Image Generation Endpoints
# =============================================================================

@router.get("/{barcode_id}/image")
def get_barcode_image(
    barcode_id: int,
    format: str = Query("png", regex="^(png|svg)$"),
    db: Session = Depends(get_db)
):
    """Get barcode image (Code128 format)."""
    barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    image_bytes = BarcodeGenerator.generate_code128_image(
        barcode.barcode_value,
        output_format=format
    )
    
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Barcode generation library not available"
        )
    
    media_type = f"image/{format}" if format == "png" else "image/svg+xml"
    return Response(content=image_bytes, media_type=media_type)


@router.get("/{barcode_id}/qr")
def get_qr_code_image(
    barcode_id: int,
    format: str = Query("png", regex="^(png|svg)$"),
    size: int = Query(10, ge=5, le=20),
    db: Session = Depends(get_db)
):
    """Get QR code image with embedded data."""
    barcode = db.query(BarcodeLabel).filter(BarcodeLabel.id == barcode_id).first()
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found")
    
    # Use QR data if available, otherwise barcode value
    import json
    qr_content = json.dumps(barcode.qr_data) if barcode.qr_data else barcode.barcode_value
    
    image_bytes = BarcodeGenerator.generate_qr_code_image(
        qr_content,
        output_format=format,
        box_size=size
    )
    
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="QR code generation library not available"
        )
    
    media_type = f"image/{format}" if format == "png" else "image/svg+xml"
    return Response(content=image_bytes, media_type=media_type)


# =============================================================================
# Summary and Reports
# =============================================================================

@router.get("/summary/by-stage", response_model=List[BarcodeSummaryByStage])
def get_summary_by_stage(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get barcode summary grouped by traceability stage."""
    results = db.query(
        BarcodeLabel.traceability_stage,
        func.count(BarcodeLabel.id).label('count'),
        func.sum(func.coalesce(BarcodeLabel.current_quantity, 0)).label('total_quantity')
    ).filter(
        BarcodeLabel.status == BarcodeStatus.ACTIVE
    ).group_by(BarcodeLabel.traceability_stage).all()
    
    return [
        BarcodeSummaryByStage(
            stage=SchemaTraceabilityStage(r.traceability_stage.value),
            count=r.count,
            total_quantity=float(r.total_quantity or 0)
        )
        for r in results
    ]


@router.get("/summary/by-po/{po_id}", response_model=BarcodeSummaryByPO)
def get_summary_by_po(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get barcode summary for a specific PO."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")
    
    barcodes = db.query(BarcodeLabel).filter(
        BarcodeLabel.purchase_order_id == po_id
    ).all()
    
    received = len([b for b in barcodes if b.traceability_stage == TraceabilityStage.RECEIVED])
    in_storage = len([b for b in barcodes if b.traceability_stage == TraceabilityStage.IN_STORAGE])
    in_production = len([b for b in barcodes if b.traceability_stage == TraceabilityStage.IN_PRODUCTION])
    completed = len([b for b in barcodes if b.traceability_stage == TraceabilityStage.COMPLETED])
    
    return BarcodeSummaryByPO(
        po_number=po.po_number,
        po_id=po.id,
        total_barcodes=len(barcodes),
        received_count=received,
        in_storage_count=in_storage,
        in_production_count=in_production,
        completed_count=completed
    )
