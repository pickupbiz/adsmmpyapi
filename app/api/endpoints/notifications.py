"""
Notification management endpoints.

Provides:
- In-app notifications for PO workflows
- Real-time alerts for PO status changes
- Configurable PO alert thresholds
- Notification preferences
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.purchase_order import PurchaseOrder, POStatus, POLineItem, GoodsReceiptNote
from app.models.material_instance import MaterialInstance, MaterialLifecycleStatus
from app.models.workflow import WorkflowInstance, WorkflowStatus
from app.schemas.dashboard import Alert, AlertSummary, AlertFilter, AlertType, AlertSeverity
from app.api.dependencies import get_current_user, require_any_role, PaginationParams
from app.core.alerts import alert_service
from app.core.notifications import notification_service
from app.core.websocket_manager import event_emitter


router = APIRouter(prefix="/notifications", tags=["Notifications"])


# =============================================================================
# Notification Configuration
# =============================================================================

@router.get("/config")
def get_notification_config(
    current_user: User = Depends(require_any_role)
):
    """Get notification configuration and thresholds."""
    from app.core.config import settings
    
    return {
        "email_enabled": getattr(settings, 'EMAIL_ENABLED', False),
        "po_auto_approve_threshold": getattr(settings, 'PO_AUTO_APPROVE_THRESHOLD', 5000.0),
        "po_standard_approval_threshold": getattr(settings, 'PO_STANDARD_APPROVAL_THRESHOLD', 25000.0),
        "po_high_value_threshold": getattr(settings, 'PO_HIGH_VALUE_THRESHOLD', 100000.0),
        "delivery_alert_days": 7,  # Alert when delivery is within 7 days
        "quantity_variance_threshold": 5.0,  # Alert if variance > 5%
        "critical_variance_threshold": 10.0,  # Critical alert if variance > 10%
    }


# =============================================================================
# PO Alert Management
# =============================================================================

@router.post("/po/{po_id}/check-delivery")
def check_po_delivery_alert(
    po_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Check and send delivery date approaching alert for a PO."""
    
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.created_by_user)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    if not po.expected_delivery_date:
        return {"message": "PO has no expected delivery date", "alert_sent": False}
    
    today = date.today()
    days_remaining = (po.expected_delivery_date - today).days
    
    # Alert if within 7 days
    if 0 <= days_remaining <= 7:
        # Get recipient (PO creator or Purchase role users)
        recipients = []
        if po.created_by_user and po.created_by_user.email:
            recipients.append((po.created_by_user.email, po.created_by_user.full_name))
        
        # Also notify Purchase role users
        purchase_users = db.query(User).filter(
            User.role == UserRole.PURCHASE
        ).all()
        for user in purchase_users:
            if user.email and (user.email, user.full_name) not in recipients:
                recipients.append((user.email, user.full_name))
        
        # Send notifications
        sent_count = 0
        for email, name in recipients:
            if notification_service.notify_po_delivery_approaching(
                recipient_email=email,
                recipient_name=name,
                po_number=po.po_number,
                supplier_name=po.supplier.name if po.supplier else "Unknown",
                expected_delivery_date=str(po.expected_delivery_date),
                days_remaining=days_remaining,
                po_url=f"/purchase-orders/{po_id}"
            ):
                sent_count += 1
        
        # Emit WebSocket alert
        background_tasks.add_task(
            event_emitter.emit_new_alert,
            AlertType.DELAYED_DELIVERY.value if days_remaining < 0 else "po_delivery_approaching",
            AlertSeverity.CRITICAL.value if days_remaining <= 3 else AlertSeverity.WARNING.value,
            f"PO {po.po_number} Delivery Approaching",
            f"PO {po.po_number} delivery is in {days_remaining} day(s)",
            "purchase_order",
            po_id
        )
        
        return {
            "message": f"Delivery alert sent to {sent_count} recipient(s)",
            "alert_sent": sent_count > 0,
            "days_remaining": days_remaining
        }
    
    return {"message": "PO delivery date is not within alert window", "alert_sent": False}


@router.post("/po/{po_id}/check-quantity-discrepancy")
def check_po_quantity_discrepancy(
    po_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Check and send quantity discrepancy alert for a PO."""
    
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.line_items),
        joinedload(PurchaseOrder.supplier)
    ).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase Order not found"
        )
    
    discrepancies = []
    sent_count = 0
    
    for line_item in po.line_items:
        if line_item.received_quantity != line_item.quantity:
            variance = line_item.quantity - line_item.received_quantity
            variance_pct = float(variance / line_item.quantity * 100) if line_item.quantity > 0 else 0
            
            # Alert if variance > 5%
            if abs(variance_pct) > 5:
                # Get material name
                from app.models.material import Material
                material = db.query(Material).filter(Material.id == line_item.material_id).first()
                material_name = material.name if material else f"Material #{line_item.material_id}"
                
                # Get recipients (Store, Purchase, Director)
                recipients = []
                store_users = db.query(User).filter(User.role == UserRole.STORE).all()
                purchase_users = db.query(User).filter(User.role == UserRole.PURCHASE).all()
                director_users = db.query(User).filter(
                    User.role.in_([UserRole.DIRECTOR, UserRole.ADMIN])
                ).all()
                
                for user in store_users + purchase_users + director_users:
                    if user.email and (user.email, user.full_name) not in recipients:
                        recipients.append((user.email, user.full_name))
                
                # Send notifications
                for email, name in recipients:
                    if notification_service.notify_po_quantity_discrepancy(
                        recipient_email=email,
                        recipient_name=name,
                        po_number=po.po_number,
                        material_name=material_name,
                        ordered_quantity=float(line_item.quantity),
                        received_quantity=float(line_item.received_quantity),
                        variance=float(variance),
                        variance_percentage=variance_pct,
                        po_url=f"/purchase-orders/{po_id}"
                    ):
                        sent_count += 1
                
                discrepancies.append({
                    "material_id": line_item.material_id,
                    "material_name": material_name,
                    "variance_percentage": variance_pct
                })
                
                # Emit WebSocket alert
                background_tasks.add_task(
                    event_emitter.emit_new_alert,
                    AlertType.QUANTITY_MISMATCH.value,
                    AlertSeverity.CRITICAL.value if abs(variance_pct) > 10 else AlertSeverity.WARNING.value,
                    f"PO {po.po_number} Quantity Discrepancy",
                    f"Material {material_name}: {variance_pct:+.1f}% variance",
                    "po_line_item",
                    line_item.id
                )
    
    return {
        "message": f"Quantity discrepancy alerts sent for {len(discrepancies)} item(s)",
        "alerts_sent": sent_count,
        "discrepancies": discrepancies
    }


@router.post("/grn/{grn_id}/receipt-confirmation")
def send_material_receipt_confirmation(
    grn_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Send material receipt confirmation notification."""
    
    grn = db.query(GoodsReceiptNote).options(
        joinedload(GoodsReceiptNote.purchase_order),
        joinedload(GoodsReceiptNote.line_items)
    ).filter(GoodsReceiptNote.id == grn_id).first()
    
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GRN not found"
        )
    
    po = grn.purchase_order
    total_items = len(grn.line_items)
    
    # Get recipients (Purchase, Store, Director)
    recipients = []
    purchase_users = db.query(User).filter(User.role == UserRole.PURCHASE).all()
    store_users = db.query(User).filter(User.role == UserRole.STORE).all()
    director_users = db.query(User).filter(
        User.role.in_([UserRole.DIRECTOR, UserRole.ADMIN])
    ).all()
    
    for user in purchase_users + store_users + director_users:
        if user.email and (user.email, user.full_name) not in recipients:
            recipients.append((user.email, user.full_name))
    
    # Send notifications
    sent_count = 0
    for email, name in recipients:
        if notification_service.notify_material_receipt_confirmation(
            recipient_email=email,
            recipient_name=name,
            grn_number=grn.grn_number,
            po_number=po.po_number if po else "N/A",
            supplier_name=po.supplier.name if po and po.supplier else "Unknown",
            received_by=current_user.full_name,
            received_date=str(grn.received_date) if grn.received_date else str(date.today()),
            total_items=total_items,
            grn_url=f"/grn/{grn_id}"
        ):
            sent_count += 1
    
    # Emit WebSocket notification
    background_tasks.add_task(
        event_emitter.emit_grn_received,
        grn_id,
        grn.grn_number,
        po.po_number if po else "N/A",
        po.supplier.name if po and po.supplier else "Unknown"
    )
    
    return {
        "message": f"Receipt confirmation sent to {sent_count} recipient(s)",
        "notifications_sent": sent_count
    }


# =============================================================================
# Automated Alert Checking
# =============================================================================

@router.post("/check-all-po-deliveries")
def check_all_po_deliveries(
    background_tasks: BackgroundTasks,
    days_ahead: int = Query(7, description="Check POs with delivery within N days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Check all POs for approaching delivery dates and send alerts."""
    
    today = date.today()
    alert_date = today + timedelta(days=days_ahead)
    
    pos = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.created_by_user)
    ).filter(
        and_(
            PurchaseOrder.expected_delivery_date >= today,
            PurchaseOrder.expected_delivery_date <= alert_date,
            PurchaseOrder.status.in_([
                POStatus.ORDERED,
                POStatus.PARTIALLY_RECEIVED
            ])
        )
    ).all()
    
    alerts_sent = 0
    for po in pos:
        days_remaining = (po.expected_delivery_date - today).days
        
        # Get recipients
        recipients = []
        if po.created_by_user and po.created_by_user.email:
            recipients.append((po.created_by_user.email, po.created_by_user.full_name))
        
        purchase_users = db.query(User).filter(User.role == UserRole.PURCHASE).all()
        for user in purchase_users:
            if user.email and (user.email, user.full_name) not in recipients:
                recipients.append((user.email, user.full_name))
        
        # Send notifications
        for email, name in recipients:
            if notification_service.notify_po_delivery_approaching(
                recipient_email=email,
                recipient_name=name,
                po_number=po.po_number,
                supplier_name=po.supplier.name if po.supplier else "Unknown",
                expected_delivery_date=str(po.expected_delivery_date),
                days_remaining=days_remaining,
                po_url=f"/purchase-orders/{po.id}"
            ):
                alerts_sent += 1
    
    return {
        "message": f"Checked {len(pos)} PO(s), sent {alerts_sent} alert(s)",
        "pos_checked": len(pos),
        "alerts_sent": alerts_sent
    }


@router.post("/check-all-quantity-discrepancies")
def check_all_quantity_discrepancies(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role)
):
    """Check all POs for quantity discrepancies and send alerts."""
    
    pos = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.line_items),
        joinedload(PurchaseOrder.supplier)
    ).filter(
        PurchaseOrder.status.in_([
            POStatus.PARTIALLY_RECEIVED,
            POStatus.FULLY_RECEIVED,
            POStatus.COMPLETED
        ])
    ).all()
    
    total_discrepancies = 0
    alerts_sent = 0
    
    for po in pos:
        for line_item in po.line_items:
            if line_item.received_quantity != line_item.quantity:
                variance = line_item.quantity - line_item.received_quantity
                variance_pct = float(variance / line_item.quantity * 100) if line_item.quantity > 0 else 0
                
                if abs(variance_pct) > 5:
                    total_discrepancies += 1
                    
                    # Get material name
                    from app.models.material import Material
                    material = db.query(Material).filter(Material.id == line_item.material_id).first()
                    material_name = material.name if material else f"Material #{line_item.material_id}"
                    
                    # Get recipients
                    recipients = []
                    store_users = db.query(User).filter(User.role == UserRole.STORE).all()
                    purchase_users = db.query(User).filter(User.role == UserRole.PURCHASE).all()
                    director_users = db.query(User).filter(
                        User.role.in_([UserRole.DIRECTOR, UserRole.ADMIN])
                    ).all()
                    
                    for user in store_users + purchase_users + director_users:
                        if user.email and (user.email, user.full_name) not in recipients:
                            recipients.append((user.email, user.full_name))
                    
                    # Send notifications
                    for email, name in recipients:
                        if notification_service.notify_po_quantity_discrepancy(
                            recipient_email=email,
                            recipient_name=name,
                            po_number=po.po_number,
                            material_name=material_name,
                            ordered_quantity=float(line_item.quantity),
                            received_quantity=float(line_item.received_quantity),
                            variance=float(variance),
                            variance_percentage=variance_pct,
                            po_url=f"/purchase-orders/{po.id}"
                        ):
                            alerts_sent += 1
    
    return {
        "message": f"Found {total_discrepancies} discrepancy(ies), sent {alerts_sent} alert(s)",
        "discrepancies_found": total_discrepancies,
        "alerts_sent": alerts_sent
    }


# =============================================================================
# Notification History
# =============================================================================

@router.get("/history")
def get_notification_history(
    current_user: User = Depends(require_any_role),
    limit: int = Query(50, le=200)
):
    """Get notification history/log."""
    
    log = notification_service.get_notification_log()
    
    # Return most recent entries
    return {
        "total_notifications": len(log),
        "notifications": log[-limit:] if len(log) > limit else log
    }


# =============================================================================
# In-App Notifications
# =============================================================================

@router.get("/in-app", response_model=AlertSummary)
def get_in_app_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
    alert_types: Optional[List[str]] = Query(None),
    severities: Optional[List[str]] = Query(None),
    unread_only: bool = False
):
    """Get in-app notifications for current user."""
    
    filter_params = None
    if alert_types or severities:
        filter_params = AlertFilter(
            types=[AlertType(t) for t in alert_types] if alert_types else None,
            severities=[AlertSeverity(s) for s in severities] if severities else None
        )
    
    # Get all alerts
    alert_summary = alert_service.get_all_alerts(db, filter_params)
    
    # Filter by user role if needed (e.g., only show relevant alerts)
    # For now, return all alerts
    
    return alert_summary
