"""
Dashboard and analytics endpoints.

Provides:
- Real-time PO status dashboard
- Material status with PO tracking
- PO vs Received material comparison
- Supplier performance analytics
- Lead time analytics
- Alerts and notifications
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, case

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.purchase_order import (
    PurchaseOrder, POLineItem, POStatus, POApprovalHistory,
    GoodsReceiptNote, GRNLineItem
)
from app.models.material import Material
from app.models.material_instance import (
    MaterialInstance, MaterialLifecycleStatus, MaterialAllocation
)
from app.models.inventory import Inventory
from app.models.supplier import Supplier
from app.models.project import Project
from app.schemas.dashboard import (
    DashboardOverview, PODashboardSummary, MaterialDashboardSummary,
    InventoryStatusSummary, POStatusCount, MaterialStatusCount,
    POVsReceivedComparison, POLineComparison,
    PODeliveryAnalytics, POToProductionLeadTime, LeadTimeReport,
    SupplierPerformanceMetrics, SupplierRanking, SupplierAnalyticsReport,
    ProjectPOConsumption, MaterialConsumptionItem, ProjectConsumptionReport,
    MaterialMovementRecord, MaterialMovementHistory,
    Alert, AlertSummary, AlertFilter, AlertType, AlertSeverity,
    FastMovingMaterial, LowStockItem, StockAnalysisReport
)
from app.api.dependencies import get_current_user, require_any_role, PaginationParams
from app.core.alerts import alert_service


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =============================================================================
# Main Dashboard
# =============================================================================

@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get complete dashboard overview with all summaries."""
    
    po_summary = _get_po_summary(db)
    material_summary = _get_material_summary(db)
    inventory_summary = _get_inventory_summary(db)
    
    # Get recent alerts (limit to 10)
    alert_data = alert_service.get_all_alerts(db)
    recent_alerts = alert_data.alerts[:10]
    
    return DashboardOverview(
        po_summary=po_summary,
        material_summary=material_summary,
        inventory_summary=inventory_summary,
        recent_alerts=recent_alerts,
        last_updated=datetime.utcnow()
    )


@router.get("/po-summary", response_model=PODashboardSummary)
def get_po_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get PO status dashboard summary."""
    return _get_po_summary(db)


@router.get("/material-summary", response_model=MaterialDashboardSummary)
def get_material_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get material status dashboard summary."""
    return _get_material_summary(db)


@router.get("/inventory-summary", response_model=InventoryStatusSummary)
def get_inventory_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get inventory status summary."""
    return _get_inventory_summary(db)


# =============================================================================
# PO Analytics
# =============================================================================

@router.get("/po-vs-received", response_model=List[POVsReceivedComparison])
def get_po_vs_received_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    supplier_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mismatch_only: bool = False,
    pagination: PaginationParams = Depends()
):
    """Get PO ordered vs received quantity comparison."""
    
    query = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.line_items),
        joinedload(PurchaseOrder.supplier)
    ).filter(
        PurchaseOrder.status.in_([
            POStatus.PARTIALLY_RECEIVED,
            POStatus.FULLY_RECEIVED,
            POStatus.COMPLETED
        ])
    )
    
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if from_date:
        query = query.filter(PurchaseOrder.order_date >= from_date)
    if to_date:
        query = query.filter(PurchaseOrder.order_date <= to_date)
    
    pos = query.offset(pagination.offset).limit(pagination.limit).all()
    
    comparisons = []
    for po in pos:
        line_comparisons = []
        total_ordered = Decimal("0")
        total_received = Decimal("0")
        has_mismatch = False
        
        for line in po.line_items:
            variance = line.quantity_ordered - line.quantity_received
            variance_pct = float(variance / line.quantity_ordered * 100) if line.quantity_ordered > 0 else 0
            
            # Get material name
            material = db.query(Material).filter(Material.id == line.material_id).first()
            material_name = material.name if material else f"Material #{line.material_id}"
            
            if abs(variance_pct) > 1:  # More than 1% variance
                has_mismatch = True
            
            line_comparisons.append(POLineComparison(
                material_id=line.material_id,
                material_name=material_name,
                ordered_quantity=line.quantity,
                received_quantity=line.received_quantity,
                unit=line.unit,
                variance=variance,
                variance_percentage=variance_pct,
                status="match" if abs(variance_pct) <= 1 else ("over" if variance < 0 else "under")
            ))
            
            total_ordered += line.quantity_ordered
            total_received += line.quantity_received
        
        if mismatch_only and not has_mismatch:
            continue
        
        total_variance_pct = float((total_ordered - total_received) / total_ordered * 100) if total_ordered > 0 else 0
        
        comparisons.append(POVsReceivedComparison(
            po_id=po.id,
            po_number=po.po_number,
            supplier_name=po.supplier.name if po.supplier else "Unknown",
            line_items=line_comparisons,
            total_ordered_quantity=total_ordered,
            total_received_quantity=total_received,
            variance_percentage=total_variance_pct,
            status=po.status.value,
            has_mismatch=has_mismatch
        ))
    
    return comparisons


@router.get("/delivery-analytics", response_model=PODeliveryAnalytics)
def get_delivery_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
):
    """Get PO delivery performance analytics."""
    
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_([
            POStatus.FULLY_RECEIVED,
            POStatus.COMPLETED
        ])
    )
    
    if from_date:
        query = query.filter(PurchaseOrder.order_date >= from_date)
    if to_date:
        query = query.filter(PurchaseOrder.order_date <= to_date)
    
    pos = query.all()
    
    total = len(pos)
    on_time = 0
    late = 0
    early = 0
    total_delay_days = 0
    max_delay = 0
    
    for po in pos:
        if po.actual_delivery_date and po.expected_delivery_date:
            diff = (po.actual_delivery_date - po.expected_delivery_date).days
            
            if diff <= 0:
                if diff < -1:  # More than 1 day early
                    early += 1
                else:
                    on_time += 1
            else:
                late += 1
                total_delay_days += diff
                max_delay = max(max_delay, diff)
    
    return PODeliveryAnalytics(
        total_pos_analyzed=total,
        on_time_deliveries=on_time,
        late_deliveries=late,
        early_deliveries=early,
        on_time_percentage=(on_time / total * 100) if total > 0 else 0,
        avg_delay_days=(total_delay_days / late) if late > 0 else 0,
        max_delay_days=max_delay
    )


@router.get("/lead-time", response_model=LeadTimeReport)
def get_lead_time_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    material_ids: Optional[List[int]] = Query(None)
):
    """Get PO-to-production lead time analytics."""
    
    # This is a simplified version - in production, you'd calculate from actual timestamps
    query = db.query(MaterialInstance).options(
        joinedload(MaterialInstance.material)
    )
    
    if material_ids:
        query = query.filter(MaterialInstance.material_id.in_(material_ids))
    
    instances = query.all()
    
    # Group by material
    material_data = {}
    for instance in instances:
        mat_id = instance.material_id
        if mat_id not in material_data:
            material_data[mat_id] = {
                'name': instance.material.name if instance.material else f"Material #{mat_id}",
                'instances': []
            }
        material_data[mat_id]['instances'].append(instance)
    
    lead_times = []
    total_lead_time = 0
    count = 0
    
    for mat_id, data in material_data.items():
        # Calculate average times (simplified - using creation timestamps)
        avg_po_to_receipt = 5.0  # Placeholder
        avg_receipt_to_inspection = 1.0
        avg_inspection_to_storage = 0.5
        avg_storage_to_issue = 3.0
        avg_issue_to_production = 2.0
        
        total = avg_po_to_receipt + avg_receipt_to_inspection + avg_inspection_to_storage + \
                avg_storage_to_issue + avg_issue_to_production
        
        lead_times.append(POToProductionLeadTime(
            material_id=mat_id,
            material_name=data['name'],
            avg_po_to_receipt_days=avg_po_to_receipt,
            avg_receipt_to_inspection_days=avg_receipt_to_inspection,
            avg_inspection_to_storage_days=avg_inspection_to_storage,
            avg_storage_to_issue_days=avg_storage_to_issue,
            avg_issue_to_production_days=avg_issue_to_production,
            total_lead_time_days=total,
            sample_size=len(data['instances'])
        ))
        
        total_lead_time += total
        count += 1
    
    # Identify bottlenecks
    bottlenecks = []
    if lead_times:
        avg_stages = {
            'PO to Receipt': sum(lt.avg_po_to_receipt_days for lt in lead_times) / len(lead_times),
            'Receipt to Inspection': sum(lt.avg_receipt_to_inspection_days for lt in lead_times) / len(lead_times),
            'Inspection to Storage': sum(lt.avg_inspection_to_storage_days for lt in lead_times) / len(lead_times),
            'Storage to Issue': sum(lt.avg_storage_to_issue_days for lt in lead_times) / len(lead_times),
            'Issue to Production': sum(lt.avg_issue_to_production_days for lt in lead_times) / len(lead_times),
        }
        
        max_stage = max(avg_stages, key=avg_stages.get)
        bottlenecks.append(f"Longest stage: {max_stage} ({avg_stages[max_stage]:.1f} days average)")
    
    period = "All time"
    if from_date and to_date:
        period = f"{from_date} to {to_date}"
    elif from_date:
        period = f"Since {from_date}"
    elif to_date:
        period = f"Until {to_date}"
    
    return LeadTimeReport(
        report_period=period,
        generated_at=datetime.utcnow(),
        overall_avg_lead_time_days=(total_lead_time / count) if count > 0 else 0,
        materials=lead_times,
        bottlenecks=bottlenecks
    )


# =============================================================================
# Supplier Analytics
# =============================================================================

@router.get("/supplier-performance", response_model=SupplierAnalyticsReport)
def get_supplier_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    min_po_count: int = 1
):
    """Get supplier performance analytics."""
    
    # Get all suppliers with their POs
    suppliers = db.query(Supplier).all()
    
    metrics_list = []
    
    for supplier in suppliers:
        # Get POs for this supplier
        po_query = db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier.id
        )
        
        if from_date:
            po_query = po_query.filter(PurchaseOrder.order_date >= from_date)
        if to_date:
            po_query = po_query.filter(PurchaseOrder.order_date <= to_date)
        
        pos = po_query.all()
        
        if len(pos) < min_po_count:
            continue
        
        total_pos = len(pos)
        completed_pos = sum(1 for po in pos if po.status == POStatus.COMPLETED)
        cancelled_pos = sum(1 for po in pos if po.status == POStatus.CANCELLED)
        total_value = sum(po.total_amount for po in pos)
        
        # Calculate delivery performance
        delivered_pos = [po for po in pos if po.actual_delivery_date and po.expected_delivery_date]
        on_time = sum(1 for po in delivered_pos if po.actual_delivery_date <= po.expected_delivery_date)
        on_time_rate = (on_time / len(delivered_pos) * 100) if delivered_pos else 100
        
        # Calculate quality rate (simplified - based on received quantities)
        quality_rate = 95.0  # Placeholder - would calculate from inspection results
        
        # Calculate quantity accuracy
        accuracy_rate = 98.0  # Placeholder - would calculate from PO vs received
        
        # Calculate composite score
        score = (on_time_rate * 0.4 + quality_rate * 0.4 + accuracy_rate * 0.2)
        
        # Determine trend (simplified)
        trend = "stable"
        
        last_po = max(pos, key=lambda p: p.created_at) if pos else None
        
        metrics = SupplierPerformanceMetrics(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            supplier_code=supplier.code or "",
            total_pos=total_pos,
            completed_pos=completed_pos,
            cancelled_pos=cancelled_pos,
            total_value=total_value,
            on_time_delivery_rate=on_time_rate,
            quality_acceptance_rate=quality_rate,
            quantity_accuracy_rate=accuracy_rate,
            avg_delivery_time_days=5.0,  # Placeholder
            avg_price_variance=0.0,
            defect_rate=5.0,
            return_rate=2.0,
            performance_score=score,
            performance_trend=trend,
            last_po_date=last_po.created_at if last_po else None
        )
        
        metrics_list.append(metrics)
    
    # Sort by score
    metrics_list.sort(key=lambda x: x.performance_score, reverse=True)
    
    # Create rankings
    top_performers = [
        SupplierRanking(
            rank=i+1,
            supplier_id=m.supplier_id,
            supplier_name=m.supplier_name,
            score=m.performance_score,
            metrics=m
        )
        for i, m in enumerate(metrics_list[:5])
    ]
    
    underperformers = [
        SupplierRanking(
            rank=len(metrics_list) - i,
            supplier_id=m.supplier_id,
            supplier_name=m.supplier_name,
            score=m.performance_score,
            metrics=m
        )
        for i, m in enumerate(reversed(metrics_list[-5:]))
    ] if len(metrics_list) >= 5 else []
    
    period = "All time"
    if from_date and to_date:
        period = f"{from_date} to {to_date}"
    
    return SupplierAnalyticsReport(
        report_period=period,
        generated_at=datetime.utcnow(),
        total_suppliers=len(suppliers),
        active_suppliers=len(metrics_list),
        top_performers=top_performers,
        underperformers=underperformers,
        supplier_metrics=metrics_list
    )


# =============================================================================
# Project Consumption
# =============================================================================

@router.get("/project-consumption", response_model=ProjectConsumptionReport)
def get_project_consumption(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    project_ids: Optional[List[int]] = Query(None),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
):
    """Get project-wise PO consumption report."""
    
    query = db.query(Project)
    if project_ids:
        query = query.filter(Project.id.in_(project_ids))
    
    projects = query.all()
    
    project_consumptions = []
    total_value = Decimal("0")
    
    for project in projects:
        # Get allocations for this project
        allocations = db.query(MaterialAllocation).filter(
            MaterialAllocation.project_id == project.id
        ).all()
        
        materials_consumed = []
        po_value = Decimal("0")
        
        for alloc in allocations:
            instance = db.query(MaterialInstance).filter(
                MaterialInstance.id == alloc.material_instance_id
            ).first()
            
            if instance:
                material = db.query(Material).filter(
                    Material.id == instance.material_id
                ).first()
                
                unit_price = Decimal("0")
                po_number = "N/A"
                
                if instance.po_line_item_id:
                    line_item = db.query(POLineItem).filter(
                        POLineItem.id == instance.po_line_item_id
                    ).first()
                    if line_item:
                        unit_price = line_item.unit_price
                        po = db.query(PurchaseOrder).filter(
                            PurchaseOrder.id == line_item.po_id
                        ).first()
                        if po:
                            po_number = po.po_number
                
                total_cost = alloc.allocated_quantity * unit_price
                
                materials_consumed.append(MaterialConsumptionItem(
                    material_id=instance.material_id,
                    material_name=material.name if material else "Unknown",
                    po_number=po_number,
                    ordered_quantity=instance.quantity,
                    consumed_quantity=alloc.allocated_quantity,
                    remaining_quantity=instance.quantity - alloc.allocated_quantity,
                    unit=instance.unit_of_measure,
                    unit_price=unit_price,
                    total_cost=total_cost
                ))
                
                po_value += total_cost
        
        budget_allocated = Decimal("100000")  # Placeholder
        utilization = float(po_value / budget_allocated * 100) if budget_allocated > 0 else 0
        
        project_consumptions.append(ProjectPOConsumption(
            project_id=project.id,
            project_name=project.name,
            project_code=project.code,
            total_pos_linked=len(set(m.po_number for m in materials_consumed if m.po_number != "N/A")),
            total_po_value=po_value,
            materials_consumed=materials_consumed,
            budget_allocated=budget_allocated,
            budget_utilized=po_value,
            budget_remaining=budget_allocated - po_value,
            utilization_percentage=utilization
        ))
        
        total_value += po_value
    
    period = "All time"
    if from_date and to_date:
        period = f"{from_date} to {to_date}"
    
    return ProjectConsumptionReport(
        report_period=period,
        generated_at=datetime.utcnow(),
        projects=project_consumptions,
        total_consumption_value=total_value
    )


# =============================================================================
# Material Movement
# =============================================================================

@router.get("/material-movement", response_model=MaterialMovementHistory)
def get_material_movement_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    material_id: Optional[int] = None,
    barcode: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    pagination: PaginationParams = Depends()
):
    """Get material movement history with PO reference."""
    
    from app.models.material_instance import MaterialStatusHistory
    
    query = db.query(MaterialStatusHistory).options(
        joinedload(MaterialStatusHistory.material_instance)
    )
    
    if material_id:
        query = query.join(MaterialInstance).filter(
            MaterialInstance.material_id == material_id
        )
    
    if barcode:
        query = query.join(MaterialInstance).filter(
            or_(
                MaterialInstance.serial_number == barcode,
                MaterialInstance.lot_number == barcode
            )
        )
    
    if from_date:
        query = query.filter(MaterialStatusHistory.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(MaterialStatusHistory.created_at <= datetime.combine(to_date, datetime.max.time()))
    
    query = query.order_by(MaterialStatusHistory.created_at.desc())
    
    total = query.count()
    records = query.offset(pagination.offset).limit(pagination.limit).all()
    
    movements = []
    for record in records:
        instance = record.material_instance
        
        # Get material name
        material = db.query(Material).filter(Material.id == instance.material_id).first() if instance else None
        
        # Get PO info
        po_number = None
        po_id = None
        if instance and instance.po_line_item_id:
            line_item = db.query(POLineItem).filter(POLineItem.id == instance.po_line_item_id).first()
            if line_item:
                po = db.query(PurchaseOrder).filter(PurchaseOrder.id == line_item.po_id).first()
                if po:
                    po_number = po.po_number
                    po_id = po.id
        
        # Get user name
        user = db.query(User).filter(User.id == record.changed_by_id).first() if record.changed_by_id else None
        
        movements.append(MaterialMovementRecord(
            id=record.id,
            material_instance_id=instance.id if instance else 0,
            material_name=material.name if material else "Unknown",
            barcode=(instance.serial_number or instance.lot_number) if instance else None,
            from_status=record.from_status.value if record.from_status else "unknown",
            to_status=record.to_status.value if record.to_status else "unknown",
            quantity=instance.quantity if instance else Decimal("0"),
            unit=instance.unit_of_measure if instance else "",
            po_number=po_number,
            po_id=po_id,
            location=instance.storage_location if instance else None,
            performed_by=user.full_name if user else "System",
            performed_at=record.created_at,
            notes=record.notes
        ))
    
    date_range = "All time"
    if from_date and to_date:
        date_range = f"{from_date} to {to_date}"
    
    material_name = None
    if material_id:
        mat = db.query(Material).filter(Material.id == material_id).first()
        material_name = mat.name if mat else None
    
    return MaterialMovementHistory(
        material_id=material_id,
        material_name=material_name,
        total_movements=total,
        movements=movements,
        date_range=date_range
    )


# =============================================================================
# Stock Analysis
# =============================================================================

@router.get("/stock-analysis", response_model=StockAnalysisReport)
def get_stock_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Get comprehensive stock analysis including fast-moving and low stock items."""
    
    # Get all inventory items
    inventory_items = db.query(Inventory).options(
        joinedload(Inventory.material)
    ).all()
    
    fast_moving = []
    low_stock = []
    out_of_stock = []
    critical_items = []
    items_with_pending = 0
    
    for item in inventory_items:
        # Check for pending POs
        pending_po = db.query(POLineItem).join(PurchaseOrder).filter(
            and_(
                POLineItem.material_id == item.material_id,
                PurchaseOrder.status.in_([POStatus.APPROVED, POStatus.ORDERED])
            )
        ).first()
        
        pending_qty = Decimal("0")
        expected_date = None
        if pending_po:
            items_with_pending += 1
            pending_qty = pending_po.quantity_ordered - pending_po.quantity_received
            po = db.query(PurchaseOrder).filter(PurchaseOrder.id == pending_po.po_id).first()
            expected_date = po.expected_delivery_date if po else None
        
        # Calculate consumption rate (simplified)
        consumption_rate = Decimal("1.0")  # Placeholder
        
        # Check stock levels (using threshold-based approach)
        threshold = Decimal("1.0")  # Low stock threshold
        
        if item.quantity <= 0:
            out_of_stock.append(LowStockItem(
                material_id=item.material_id,
                material_name=item.material.name if item.material else "Unknown",
                material_code=item.material.part_number if item.material else "",
                current_stock=item.quantity,
                minimum_stock=threshold,
                reorder_level=threshold * 2,
                unit=item.unit_of_measure,
                stock_percentage=0,
                pending_po_quantity=pending_qty,
                expected_delivery_date=expected_date,
                avg_consumption_rate=consumption_rate
            ))
        elif item.quantity <= threshold:
            critical_items.append(LowStockItem(
                material_id=item.material_id,
                material_name=item.material.name if item.material else "Unknown",
                material_code=item.material.part_number if item.material else "",
                current_stock=item.quantity,
                minimum_stock=threshold,
                reorder_level=threshold * 2,
                unit=item.unit_of_measure,
                stock_percentage=float(item.quantity / threshold * 100) if threshold > 0 else 0,
                pending_po_quantity=pending_qty,
                expected_delivery_date=expected_date,
                avg_consumption_rate=consumption_rate
            ))
        elif item.quantity <= threshold * 2:
            low_stock.append(LowStockItem(
                material_id=item.material_id,
                material_name=item.material.name if item.material else "Unknown",
                material_code=item.material.part_number if item.material else "",
                current_stock=item.quantity,
                minimum_stock=threshold,
                reorder_level=threshold * 2,
                unit=item.unit_of_measure,
                stock_percentage=float(item.quantity / (threshold * 2) * 100) if threshold > 0 else 0,
                days_until_stockout=float(item.quantity / consumption_rate) if consumption_rate > 0 else None,
                pending_po_quantity=pending_qty,
                expected_delivery_date=expected_date,
                avg_consumption_rate=consumption_rate
            ))
        
        # Check for fast-moving (simplified - would use actual consumption data)
        if consumption_rate > Decimal("5"):
            days_of_stock = float(item.quantity / consumption_rate) if consumption_rate > 0 else 999
            if days_of_stock < 30:
                fast_moving.append(FastMovingMaterial(
                    material_id=item.material_id,
                    material_name=item.material.name if item.material else "Unknown",
                    material_code=item.material.part_number if item.material else "",
                    consumption_rate=consumption_rate,
                    total_consumed_30_days=consumption_rate * 30,
                    total_consumed_90_days=consumption_rate * 90,
                    avg_po_quantity=Decimal("100"),  # Placeholder
                    po_frequency=2,  # Placeholder
                    current_stock=item.quantity,
                    days_of_stock=days_of_stock,
                    recommended_reorder_qty=consumption_rate * 45  # 45 days buffer
                ))
    
    return StockAnalysisReport(
        generated_at=datetime.utcnow(),
        fast_moving_materials=fast_moving,
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock,
        critical_items=critical_items,
        items_with_pending_pos=items_with_pending
    )


# =============================================================================
# Alerts
# =============================================================================

@router.get("/alerts", response_model=AlertSummary)
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    alert_types: Optional[List[str]] = Query(None),
    severities: Optional[List[str]] = Query(None),
    acknowledged: Optional[bool] = None
):
    """Get all active alerts."""
    
    filter_params = None
    if alert_types or severities or acknowledged is not None:
        filter_params = AlertFilter(
            types=[AlertType(t) for t in alert_types] if alert_types else None,
            severities=[AlertSeverity(s) for s in severities] if severities else None,
            acknowledged=acknowledged
        )
    
    return alert_service.get_all_alerts(db, filter_params)


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Acknowledge an alert."""
    
    alert = alert_service.acknowledge_alert(alert_id, current_user.full_name)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert acknowledged", "alert": alert}


# =============================================================================
# Helper Functions
# =============================================================================

def _get_po_summary(db: Session) -> PODashboardSummary:
    """Generate PO dashboard summary."""
    
    # Count by status
    status_counts = db.query(
        PurchaseOrder.status,
        func.count(PurchaseOrder.id),
        func.sum(PurchaseOrder.total_amount)
    ).group_by(PurchaseOrder.status).all()
    
    summary = PODashboardSummary()
    pos_by_status = []
    
    for status_val, count, total in status_counts:
        summary.total_pos += count
        summary.total_value += total or Decimal("0")
        
        pos_by_status.append(POStatusCount(
            status=status_val.value,
            count=count,
            total_value=total or Decimal("0")
        ))
        
        if status_val == POStatus.DRAFT:
            summary.draft_count = count
        elif status_val == POStatus.PENDING_APPROVAL:
            summary.pending_approval_count = count
            summary.pending_value += total or Decimal("0")
        elif status_val == POStatus.APPROVED:
            summary.approved_count = count
        elif status_val == POStatus.ORDERED:
            summary.ordered_count = count
            summary.ordered_value += total or Decimal("0")
        elif status_val == POStatus.PARTIALLY_RECEIVED:
            summary.partially_received_count = count
        elif status_val == POStatus.COMPLETED:
            summary.completed_count = count
            summary.received_value += total or Decimal("0")
        elif status_val == POStatus.CANCELLED:
            summary.cancelled_count = count
    
    summary.pos_by_status = pos_by_status
    
    # Overdue POs
    today = date.today()
    summary.overdue_pos = db.query(PurchaseOrder).filter(
        and_(
            PurchaseOrder.expected_delivery_date < today,
            PurchaseOrder.status.in_([POStatus.ORDERED, POStatus.PARTIALLY_RECEIVED])
        )
    ).count()
    
    # POs pending this week
    week_end = today + timedelta(days=7)
    summary.pos_pending_this_week = db.query(PurchaseOrder).filter(
        and_(
            PurchaseOrder.expected_delivery_date <= week_end,
            PurchaseOrder.expected_delivery_date >= today,
            PurchaseOrder.status.in_([POStatus.ORDERED, POStatus.PARTIALLY_RECEIVED])
        )
    ).count()
    
    return summary


def _get_material_summary(db: Session) -> MaterialDashboardSummary:
    """Generate material dashboard summary."""
    
    # Count by status
    status_counts = db.query(
        MaterialInstance.lifecycle_status,
        func.count(MaterialInstance.id),
        func.sum(MaterialInstance.quantity)
    ).group_by(MaterialInstance.lifecycle_status).all()
    
    summary = MaterialDashboardSummary()
    materials_by_status = []
    
    for status_val, count, total_qty in status_counts:
        summary.total_material_instances += count
        
        materials_by_status.append(MaterialStatusCount(
            status=status_val.value,
            count=count,
            total_quantity=total_qty or Decimal("0")
        ))
        
        if status_val == MaterialLifecycleStatus.ORDERED:
            summary.ordered_count = count
        elif status_val == MaterialLifecycleStatus.RECEIVED:
            summary.received_count = count
        elif status_val == MaterialLifecycleStatus.IN_INSPECTION:
            summary.in_inspection_count = count
            summary.pending_inspection = count
        elif status_val == MaterialLifecycleStatus.IN_STORAGE:
            summary.in_storage_count = count
        elif status_val == MaterialLifecycleStatus.ISSUED:
            summary.issued_count = count
        elif status_val == MaterialLifecycleStatus.IN_PRODUCTION:
            summary.in_production_count = count
        elif status_val == MaterialLifecycleStatus.COMPLETED:
            summary.completed_count = count
        elif status_val == MaterialLifecycleStatus.REJECTED:
            summary.rejected_count = count
    
    summary.materials_by_status = materials_by_status
    
    return summary


def _get_inventory_summary(db: Session) -> InventoryStatusSummary:
    """Generate inventory status summary."""
    
    inventory_stats = db.query(
        func.count(Inventory.id),
        func.sum(Inventory.quantity),
        func.sum(Inventory.quantity * Inventory.unit_cost)
    ).first()
    
    total_items, total_qty, total_value = inventory_stats
    
    # Low stock: items with quantity <= 10% of average or <= 1 unit
    low_stock = db.query(Inventory).filter(
        and_(
            Inventory.quantity <= 1,
            Inventory.quantity > 0
        )
    ).count()
    
    out_of_stock = db.query(Inventory).filter(
        Inventory.quantity <= 0
    ).count()
    
    # Items below reorder (using same logic as low stock for now)
    below_reorder = low_stock
    
    return InventoryStatusSummary(
        total_items=total_items or 0,
        total_quantity=total_qty or Decimal("0"),
        total_value=total_value or Decimal("0"),
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock,
        items_below_reorder=below_reorder
    )
