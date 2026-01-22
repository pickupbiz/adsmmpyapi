"""
Report generation and export endpoints.

Provides:
- PDF report generation
- Excel report generation
- CSV export
- Report download endpoints
"""
import os
from datetime import datetime, date, timedelta
from typing import Optional, List
from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
import io
import csv

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.material import Material
from app.models.material_instance import MaterialInstance, MaterialLifecycleStatus
from app.models.inventory import Inventory
from app.models.supplier import Supplier
from app.models.project import Project
from app.schemas.dashboard import (
    ReportFormat, DateRange,
    POReportRequest, MaterialReportRequest, 
    ProjectReportRequest, SupplierReportRequest,
    ReportResponse
)
from app.api.dependencies import get_current_user, require_any_role, PaginationParams
from app.core.report_generator import pdf_generator, excel_generator


router = APIRouter(prefix="/reports", tags=["Reports"])


# =============================================================================
# Report Generation
# =============================================================================

@router.post("/po", response_model=ReportResponse)
def generate_po_report(
    request: POReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Generate Purchase Order report in specified format."""
    
    # Build date range
    start_date, end_date = _get_date_range(request.date_range, request.start_date, request.end_date)
    
    # Query POs
    query = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.line_items),
        joinedload(PurchaseOrder.supplier)
    )
    
    if start_date:
        query = query.filter(PurchaseOrder.order_date >= start_date)
    if end_date:
        query = query.filter(PurchaseOrder.order_date <= end_date)
    if request.supplier_ids:
        query = query.filter(PurchaseOrder.supplier_id.in_(request.supplier_ids))
    if request.status_filter:
        statuses = [POStatus(s) for s in request.status_filter]
        query = query.filter(PurchaseOrder.status.in_(statuses))
    
    pos = query.order_by(PurchaseOrder.order_date.desc()).all()
    
    # Convert to dict for report generator
    po_data = []
    for po in pos:
        po_dict = {
            'po_number': po.po_number,
            'supplier_name': po.supplier.name if po.supplier else 'Unknown',
            'order_date': po.order_date,
            'expected_delivery_date': po.expected_delivery_date,
            'status': po.status.value,
            'priority': po.priority.value if po.priority else 'normal',
            'total_amount': float(po.total_amount),
            'created_by': po.created_by_id
        }
        
        if request.include_line_items:
            po_dict['line_items'] = []
            for line in po.line_items:
                material = db.query(Material).filter(Material.id == line.material_id).first()
                po_dict['line_items'].append({
                    'material_name': material.name if material else f'Material #{line.material_id}',
                    'quantity': float(line.quantity_ordered),
                    'unit': line.unit,
                    'unit_price': float(line.unit_price),
                    'total_price': float(line.total_price),
                    'received_quantity': float(line.quantity_received),
                    'status': line.status.value if line.status else 'pending'
                })
        
        po_data.append(po_dict)
    
    # Generate report
    report_id = str(uuid4())[:8]
    
    if request.format == ReportFormat.PDF:
        filepath = pdf_generator.generate_po_report(po_data, "Purchase Order Report")
        filename = os.path.basename(filepath)
    elif request.format == ReportFormat.EXCEL:
        filepath = excel_generator.generate_po_report(po_data, "Purchase Order Report")
        filename = os.path.basename(filepath)
    else:  # CSV
        filepath, filename = _generate_csv_report(po_data, "po_report", [
            'po_number', 'supplier_name', 'order_date', 'expected_delivery_date',
            'status', 'priority', 'total_amount'
        ])
    
    return ReportResponse(
        report_id=report_id,
        report_name=filename,
        format=request.format,
        generated_at=datetime.utcnow(),
        file_url=f"/api/v1/reports/download/{filename}",
        file_size_bytes=os.path.getsize(filepath),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )


@router.post("/materials", response_model=ReportResponse)
def generate_material_report(
    request: MaterialReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Generate Material status report in specified format."""
    
    start_date, end_date = _get_date_range(request.date_range, request.start_date, request.end_date)
    
    # Query material instances
    query = db.query(MaterialInstance).options(
        joinedload(MaterialInstance.material)
    )
    
    if start_date:
        query = query.filter(MaterialInstance.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(MaterialInstance.created_at <= datetime.combine(end_date, datetime.max.time()))
    if request.material_ids:
        query = query.filter(MaterialInstance.material_id.in_(request.material_ids))
    if request.status_filter:
        statuses = [MaterialLifecycleStatus(s) for s in request.status_filter]
        query = query.filter(MaterialInstance.lifecycle_status.in_(statuses))
    
    instances = query.order_by(MaterialInstance.created_at.desc()).all()
    
    # Convert to dict
    material_data = []
    for inst in instances:
        # Get PO info
        po_number = "N/A"
        if inst.po_line_item_id:
            line_item = db.query(POLineItem).filter(POLineItem.id == inst.po_line_item_id).first()
            if line_item:
                po = db.query(PurchaseOrder).filter(PurchaseOrder.id == line_item.po_id).first()
                if po:
                    po_number = po.po_number
        
        material_data.append({
            'material_id': inst.material_id,
            'material_name': inst.material.name if inst.material else f'Material #{inst.material_id}',
            'barcode': inst.serial_number or inst.lot_number or '',
            'po_number': po_number,
            'status': inst.lifecycle_status.value,
            'quantity': float(inst.quantity),
            'unit': inst.unit_of_measure,
            'location': inst.storage_location or 'N/A',
            'updated_at': inst.updated_at
        })
    
    # Generate report
    report_id = str(uuid4())[:8]
    
    if request.format == ReportFormat.PDF:
        filepath = pdf_generator.generate_material_report(material_data, "Material Status Report")
        filename = os.path.basename(filepath)
    elif request.format == ReportFormat.EXCEL:
        filepath = excel_generator.generate_material_report(material_data, "Material Status Report")
        filename = os.path.basename(filepath)
    else:  # CSV
        filepath, filename = _generate_csv_report(material_data, "material_report", [
            'material_id', 'material_name', 'barcode', 'po_number',
            'status', 'quantity', 'unit', 'location'
        ])
    
    return ReportResponse(
        report_id=report_id,
        report_name=filename,
        format=request.format,
        generated_at=datetime.utcnow(),
        file_url=f"/api/v1/reports/download/{filename}",
        file_size_bytes=os.path.getsize(filepath)
    )


@router.post("/inventory", response_model=ReportResponse)
def generate_inventory_report(
    format: ReportFormat = ReportFormat.EXCEL,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Generate Inventory status report."""
    
    # Query inventory
    inventory_items = db.query(Inventory).options(
        joinedload(Inventory.material)
    ).all()
    
    # Check for pending POs
    inventory_data = []
    for item in inventory_items:
        pending_po = db.query(POLineItem).join(PurchaseOrder).filter(
            and_(
                POLineItem.material_id == item.material_id,
                PurchaseOrder.status.in_([POStatus.APPROVED, POStatus.ORDERED])
            )
        ).first()
        
        inventory_data.append({
            'material_id': item.material_id,
            'material_name': item.material.name if item.material else f'Material #{item.material_id}',
            'quantity': float(item.quantity),
            'unit': item.unit,
            'minimum_stock': float(item.minimum_stock),
            'reorder_level': float(item.reorder_level),
            'location': item.location or 'Default',
            'has_pending_po': pending_po is not None
        })
    
    # Generate report
    report_id = str(uuid4())[:8]
    
    if format == ReportFormat.PDF:
        filepath = pdf_generator.generate_inventory_report(inventory_data, "Inventory Status Report")
        filename = os.path.basename(filepath)
    elif format == ReportFormat.EXCEL:
        filepath = excel_generator.generate_inventory_report(inventory_data, "Inventory Status Report")
        filename = os.path.basename(filepath)
    else:  # CSV
        filepath, filename = _generate_csv_report(inventory_data, "inventory_report", [
            'material_id', 'material_name', 'quantity', 'unit',
            'minimum_stock', 'reorder_level', 'location', 'has_pending_po'
        ])
    
    return ReportResponse(
        report_id=report_id,
        report_name=filename,
        format=format,
        generated_at=datetime.utcnow(),
        file_url=f"/api/v1/reports/download/{filename}",
        file_size_bytes=os.path.getsize(filepath)
    )


@router.post("/suppliers", response_model=ReportResponse)
def generate_supplier_report(
    request: SupplierReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Generate Supplier performance report."""
    
    start_date, end_date = _get_date_range(request.date_range, request.start_date, request.end_date)
    
    # Get suppliers
    suppliers = db.query(Supplier).all()
    
    supplier_data = []
    for supplier in suppliers:
        # Get PO stats
        po_query = db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier.id
        )
        
        if start_date:
            po_query = po_query.filter(PurchaseOrder.order_date >= start_date)
        if end_date:
            po_query = po_query.filter(PurchaseOrder.order_date <= end_date)
        
        pos = po_query.all()
        
        if len(pos) < request.min_po_count:
            continue
        
        total_pos = len(pos)
        completed = sum(1 for po in pos if po.status == POStatus.COMPLETED)
        total_value = sum(po.total_amount for po in pos)
        
        # Calculate on-time rate
        delivered = [po for po in pos if po.actual_delivery_date and po.expected_delivery_date]
        on_time = sum(1 for po in delivered if po.actual_delivery_date <= po.expected_delivery_date)
        on_time_rate = (on_time / len(delivered) * 100) if delivered else 100
        
        supplier_data.append({
            'supplier_name': supplier.name,
            'supplier_code': supplier.code or '',
            'total_pos': total_pos,
            'completed_pos': completed,
            'total_value': float(total_value),
            'on_time_delivery_rate': on_time_rate,
            'quality_acceptance_rate': 95.0,  # Placeholder
            'quantity_accuracy_rate': 98.0,  # Placeholder
            'performance_score': on_time_rate * 0.5 + 95.0 * 0.3 + 98.0 * 0.2,
            'performance_trend': 'stable'
        })
    
    # Sort by score
    supplier_data.sort(key=lambda x: x['performance_score'], reverse=True)
    
    # Generate report
    report_id = str(uuid4())[:8]
    
    if request.format == ReportFormat.PDF:
        filepath = pdf_generator.generate_supplier_performance_report(supplier_data, "Supplier Performance Report")
        filename = os.path.basename(filepath)
    elif request.format == ReportFormat.EXCEL:
        filepath = excel_generator.generate_supplier_performance_report(supplier_data, "Supplier Performance Report")
        filename = os.path.basename(filepath)
    else:  # CSV
        filepath, filename = _generate_csv_report(supplier_data, "supplier_report", [
            'supplier_name', 'supplier_code', 'total_pos', 'completed_pos',
            'total_value', 'on_time_delivery_rate', 'performance_score'
        ])
    
    return ReportResponse(
        report_id=report_id,
        report_name=filename,
        format=request.format,
        generated_at=datetime.utcnow(),
        file_url=f"/api/v1/reports/download/{filename}",
        file_size_bytes=os.path.getsize(filepath)
    )


@router.post("/project-consumption", response_model=ReportResponse)
def generate_project_consumption_report(
    request: ProjectReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Generate project consumption report."""
    
    from app.models.material_instance import MaterialAllocation
    
    # Get projects
    query = db.query(Project)
    if request.project_ids:
        query = query.filter(Project.id.in_(request.project_ids))
    
    projects = query.all()
    
    project_data = []
    for project in projects:
        allocations = db.query(MaterialAllocation).filter(
            MaterialAllocation.project_id == project.id
        ).all()
        
        total_value = Decimal("0")
        materials = []
        
        for alloc in allocations:
            instance = db.query(MaterialInstance).filter(
                MaterialInstance.id == alloc.material_instance_id
            ).first()
            
            if instance:
                material = db.query(Material).filter(Material.id == instance.material_id).first()
                
                unit_price = Decimal("0")
                po_number = "N/A"
                if instance.po_line_item_id:
                    line = db.query(POLineItem).filter(POLineItem.id == instance.po_line_item_id).first()
                    if line:
                        unit_price = line.unit_price
                        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == line.po_id).first()
                        if po:
                            po_number = po.po_number
                
                cost = alloc.allocated_quantity * unit_price
                total_value += cost
                
                materials.append({
                    'material_name': material.name if material else 'Unknown',
                    'po_number': po_number,
                    'quantity': float(alloc.allocated_quantity),
                    'unit_price': float(unit_price),
                    'total_cost': float(cost)
                })
        
        project_data.append({
            'project_name': project.name,
            'project_code': project.code,
            'total_materials': len(materials),
            'total_value': float(total_value),
            'materials': materials if request.include_bom_details else []
        })
    
    # Generate report (simplified to Excel for now)
    report_id = str(uuid4())[:8]
    
    # Flatten for CSV/simple report
    flat_data = []
    for proj in project_data:
        for mat in proj.get('materials', []):
            flat_data.append({
                'project_name': proj['project_name'],
                'project_code': proj['project_code'],
                **mat
            })
    
    if not flat_data:
        flat_data = project_data
    
    if request.format == ReportFormat.PDF:
        # Use simple dict format
        filepath = pdf_generator.generate_po_report([{
            'po_number': p['project_code'],
            'supplier_name': p['project_name'],
            'order_date': '',
            'status': '',
            'total_amount': p['total_value']
        } for p in project_data], "Project Consumption Report")
        filename = os.path.basename(filepath)
    else:  # Excel or CSV
        filepath, filename = _generate_csv_report(flat_data, "project_consumption", [
            'project_name', 'project_code', 'material_name', 'po_number',
            'quantity', 'unit_price', 'total_cost'
        ])
    
    return ReportResponse(
        report_id=report_id,
        report_name=filename,
        format=request.format,
        generated_at=datetime.utcnow(),
        file_url=f"/api/v1/reports/download/{filename}",
        file_size_bytes=os.path.getsize(filepath) if os.path.exists(filepath) else 0
    )


# =============================================================================
# Report Download
# =============================================================================

@router.get("/download/{filename}")
def download_report(
    filename: str,
    current_user: User = Depends(require_any_role)
):
    """Download a generated report."""
    
    # Validate filename to prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    # Check reports directory
    reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'reports')
    filepath = os.path.join(reports_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or expired"
        )
    
    # Determine content type
    if filename.endswith('.pdf'):
        media_type = "application/pdf"
    elif filename.endswith('.xlsx'):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith('.csv'):
        media_type = "text/csv"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        filepath,
        media_type=media_type,
        filename=filename
    )


# =============================================================================
# Quick Exports (CSV Streaming)
# =============================================================================

@router.get("/export/po-csv")
def export_pos_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    status_filter: Optional[str] = None
):
    """Quick CSV export of POs (streaming)."""
    
    query = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier)
    )
    
    if status_filter:
        query = query.filter(PurchaseOrder.status == POStatus(status_filter))
    
    pos = query.all()
    
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['PO Number', 'Supplier', 'Order Date', 'Expected Delivery', 
                        'Status', 'Total Amount'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        # Data
        for po in pos:
            writer.writerow([
                po.po_number,
                po.supplier.name if po.supplier else 'Unknown',
                str(po.order_date) if po.order_date else '',
                str(po.expected_delivery_date) if po.expected_delivery_date else '',
                po.status.value,
                f"{float(po.total_amount):.2f}"
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=po_export_{date.today()}.csv"}
    )


@router.get("/export/inventory-csv")
def export_inventory_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Quick CSV export of inventory (streaming)."""
    
    items = db.query(Inventory).options(
        joinedload(Inventory.material)
    ).all()
    
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Material ID', 'Material Name', 'Quantity', 'Unit', 
                        'Min Stock', 'Reorder Level', 'Location'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        # Data
        for item in items:
            writer.writerow([
                item.material_id,
                item.material.name if item.material else 'Unknown',
                f"{float(item.quantity):.2f}",
                item.unit,
                f"{float(item.minimum_stock):.2f}",
                f"{float(item.reorder_level):.2f}",
                item.location or 'Default'
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inventory_export_{date.today()}.csv"}
    )


@router.get("/export/materials-csv")
def export_materials_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    status_filter: Optional[str] = None
):
    """Quick CSV export of material instances (streaming)."""
    
    query = db.query(MaterialInstance).options(
        joinedload(MaterialInstance.material)
    )
    
    if status_filter:
        query = query.filter(MaterialInstance.lifecycle_status == MaterialLifecycleStatus(status_filter))
    
    instances = query.all()
    
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['ID', 'Material Name', 'Barcode', 'Status', 
                        'Quantity', 'Unit', 'Location', 'Created At'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        # Data
        for inst in instances:
            writer.writerow([
                inst.id,
                inst.material.name if inst.material else 'Unknown',
                inst.serial_number or inst.lot_number or '',
                inst.lifecycle_status.value,
                f"{float(inst.quantity):.2f}",
                inst.unit_of_measure,
                inst.storage_location or '',
                str(inst.created_at)[:19] if inst.created_at else ''
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=materials_export_{date.today()}.csv"}
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _get_date_range(
    date_range: DateRange,
    custom_start: Optional[date] = None,
    custom_end: Optional[date] = None
) -> tuple:
    """Convert DateRange enum to actual dates."""
    
    today = date.today()
    
    if date_range == DateRange.CUSTOM:
        return custom_start, custom_end
    elif date_range == DateRange.TODAY:
        return today, today
    elif date_range == DateRange.YESTERDAY:
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif date_range == DateRange.LAST_7_DAYS:
        return today - timedelta(days=7), today
    elif date_range == DateRange.LAST_30_DAYS:
        return today - timedelta(days=30), today
    elif date_range == DateRange.THIS_MONTH:
        return date(today.year, today.month, 1), today
    elif date_range == DateRange.LAST_MONTH:
        first_of_month = date(today.year, today.month, 1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = date(last_month_end.year, last_month_end.month, 1)
        return last_month_start, last_month_end
    elif date_range == DateRange.THIS_QUARTER:
        quarter = (today.month - 1) // 3
        quarter_start = date(today.year, quarter * 3 + 1, 1)
        return quarter_start, today
    elif date_range == DateRange.THIS_YEAR:
        return date(today.year, 1, 1), today
    
    return None, None


def _generate_csv_report(data: list, report_name: str, columns: list) -> tuple:
    """Generate a CSV report file."""
    
    reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{report_name}_{timestamp}.csv"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    return filepath, filename
