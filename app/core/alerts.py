"""
Alerts service for monitoring PO, material, and inventory status.

Provides real-time alert generation for:
- PO pending approvals
- Quantity mismatches
- Delayed deliveries
- Fast-moving materials
- Low stock situations
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.purchase_order import PurchaseOrder, POStatus, POLineItem, GoodsReceiptNote
from app.models.material import Material
from app.models.material_instance import MaterialInstance, MaterialLifecycleStatus
from app.models.inventory import Inventory
from app.models.workflow import WorkflowInstance, WorkflowStatus
from app.schemas.dashboard import (
    Alert, AlertType, AlertSeverity, AlertSummary, AlertFilter,
    LowStockItem, FastMovingMaterial
)


class AlertService:
    """Service for generating and managing alerts."""
    
    def __init__(self):
        self._alerts_cache: Dict[str, Alert] = {}
        self._last_refresh: Optional[datetime] = None
        self._refresh_interval = timedelta(minutes=5)
    
    def generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        return str(uuid4())[:8]
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        entity_reference: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            id=self.generate_alert_id(),
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_reference,
            data=data or {},
            created_at=datetime.utcnow()
        )
        self._alerts_cache[alert.id] = alert
        return alert
    
    def get_po_pending_approval_alerts(self, db: Session) -> List[Alert]:
        """Get alerts for POs pending approval."""
        alerts = []
        
        # Find POs pending approval
        pending_pos = db.query(PurchaseOrder).filter(
            PurchaseOrder.status == POStatus.PENDING_APPROVAL
        ).all()
        
        for po in pending_pos:
            # Calculate how long it's been pending
            days_pending = (datetime.utcnow() - po.created_at).days
            
            if days_pending > 3:
                severity = AlertSeverity.CRITICAL
            elif days_pending > 1:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
            
            alert = self.create_alert(
                alert_type=AlertType.PO_PENDING_APPROVAL,
                severity=severity,
                title=f"PO {po.po_number} Pending Approval",
                message=f"Purchase Order {po.po_number} has been pending approval for {days_pending} day(s). Total value: ${po.total_amount:,.2f}",
                entity_type="purchase_order",
                entity_id=po.id,
                entity_reference=po.po_number,
                data={
                    "days_pending": days_pending,
                    "total_amount": float(po.total_amount),
                    "supplier_id": po.supplier_id,
                    "created_at": po.created_at.isoformat()
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def get_quantity_mismatch_alerts(self, db: Session) -> List[Alert]:
        """Get alerts for PO vs received quantity mismatches."""
        alerts = []
        
        # Find POs with received items
        pos_with_receipts = db.query(PurchaseOrder).filter(
            PurchaseOrder.status.in_([
                POStatus.PARTIALLY_RECEIVED,
                POStatus.FULLY_RECEIVED,
                POStatus.COMPLETED
            ])
        ).all()
        
        for po in pos_with_receipts:
            for line_item in po.line_items:
                if line_item.received_quantity != line_item.quantity:
                    variance = line_item.quantity - line_item.received_quantity
                    variance_pct = (variance / line_item.quantity * 100) if line_item.quantity > 0 else 0
                    
                    if abs(variance_pct) > 10:
                        severity = AlertSeverity.CRITICAL
                    elif abs(variance_pct) > 5:
                        severity = AlertSeverity.WARNING
                    else:
                        continue  # Skip minor variances
                    
                    alert = self.create_alert(
                        alert_type=AlertType.QUANTITY_MISMATCH,
                        severity=severity,
                        title=f"Quantity Mismatch on PO {po.po_number}",
                        message=f"Material ID {line_item.material_id}: Ordered {line_item.quantity}, Received {line_item.received_quantity} ({variance_pct:.1f}% variance)",
                        entity_type="po_line_item",
                        entity_id=line_item.id,
                        entity_reference=po.po_number,
                        data={
                            "po_id": po.id,
                            "material_id": line_item.material_id,
                            "ordered_quantity": float(line_item.quantity),
                            "received_quantity": float(line_item.received_quantity),
                            "variance": float(variance),
                            "variance_percentage": float(variance_pct)
                        }
                    )
                    alerts.append(alert)
        
        return alerts
    
    def get_delayed_delivery_alerts(self, db: Session) -> List[Alert]:
        """Get alerts for delayed PO deliveries."""
        alerts = []
        today = datetime.utcnow().date()
        
        # Find overdue POs
        overdue_pos = db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.expected_delivery_date < today,
                PurchaseOrder.status.in_([
                    POStatus.ORDERED,
                    POStatus.PARTIALLY_RECEIVED
                ])
            )
        ).all()
        
        for po in overdue_pos:
            days_overdue = (today - po.expected_delivery_date).days
            
            if days_overdue > 7:
                severity = AlertSeverity.CRITICAL
            elif days_overdue > 3:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
            
            alert = self.create_alert(
                alert_type=AlertType.DELAYED_DELIVERY,
                severity=severity,
                title=f"PO {po.po_number} Delivery Delayed",
                message=f"Purchase Order {po.po_number} is {days_overdue} day(s) overdue. Expected: {po.expected_delivery_date}",
                entity_type="purchase_order",
                entity_id=po.id,
                entity_reference=po.po_number,
                data={
                    "days_overdue": days_overdue,
                    "expected_date": po.expected_delivery_date.isoformat(),
                    "supplier_id": po.supplier_id
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def get_low_stock_alerts(self, db: Session) -> List[Alert]:
        """Get alerts for low stock situations."""
        alerts = []
        
        # Find items below reorder level
        low_stock_items = db.query(Inventory).filter(
            Inventory.quantity <= Inventory.reorder_level
        ).all()
        
        for item in low_stock_items:
            # Check if there's a pending PO for this material
            pending_po = db.query(POLineItem).join(PurchaseOrder).filter(
                and_(
                    POLineItem.material_id == item.material_id,
                    PurchaseOrder.status.in_([
                        POStatus.APPROVED,
                        POStatus.ORDERED,
                        POStatus.PARTIALLY_RECEIVED
                    ])
                )
            ).first()
            
            if item.quantity <= item.minimum_stock:
                severity = AlertSeverity.CRITICAL
            else:
                severity = AlertSeverity.WARNING
            
            message = f"Inventory for material ID {item.material_id} is low: {item.quantity} {item.unit} (reorder level: {item.reorder_level})"
            if pending_po:
                message += f" - PO pending"
            
            alert = self.create_alert(
                alert_type=AlertType.LOW_STOCK,
                severity=severity,
                title=f"Low Stock Alert - Material {item.material_id}",
                message=message,
                entity_type="inventory",
                entity_id=item.id,
                data={
                    "material_id": item.material_id,
                    "current_quantity": float(item.quantity),
                    "minimum_stock": float(item.minimum_stock),
                    "reorder_level": float(item.reorder_level),
                    "has_pending_po": pending_po is not None
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def get_fast_moving_material_alerts(self, db: Session, threshold_days: int = 14) -> List[Alert]:
        """Get alerts for fast-moving materials that may need attention."""
        alerts = []
        
        # Find materials with high consumption rate
        # This is a simplified version - in production, you'd want more sophisticated analysis
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Get materials with significant movement in last 30 days
        material_movements = db.query(
            MaterialInstance.material_id,
            func.sum(MaterialInstance.quantity).label('total_consumed')
        ).filter(
            and_(
                MaterialInstance.status == MaterialLifecycleStatus.ISSUED,
                MaterialInstance.updated_at >= cutoff_date
            )
        ).group_by(MaterialInstance.material_id).all()
        
        for material_id, total_consumed in material_movements:
            if total_consumed is None:
                continue
                
            # Check current stock
            inventory = db.query(Inventory).filter(
                Inventory.material_id == material_id
            ).first()
            
            if inventory:
                consumption_rate = float(total_consumed) / 30  # Daily rate
                if consumption_rate > 0:
                    days_of_stock = float(inventory.quantity) / consumption_rate
                    
                    if days_of_stock <= threshold_days:
                        if days_of_stock <= 7:
                            severity = AlertSeverity.CRITICAL
                        else:
                            severity = AlertSeverity.WARNING
                        
                        alert = self.create_alert(
                            alert_type=AlertType.FAST_MOVING_MATERIAL,
                            severity=severity,
                            title=f"Fast-Moving Material Alert",
                            message=f"Material ID {material_id} has only {days_of_stock:.1f} days of stock remaining based on consumption rate",
                            entity_type="material",
                            entity_id=material_id,
                            data={
                                "material_id": material_id,
                                "daily_consumption_rate": consumption_rate,
                                "current_stock": float(inventory.quantity),
                                "days_of_stock": days_of_stock,
                                "total_consumed_30_days": float(total_consumed)
                            }
                        )
                        alerts.append(alert)
        
        return alerts
    
    def get_inspection_pending_alerts(self, db: Session) -> List[Alert]:
        """Get alerts for materials pending inspection."""
        alerts = []
        
        pending_inspection = db.query(MaterialInstance).filter(
            MaterialInstance.status == MaterialLifecycleStatus.IN_INSPECTION
        ).all()
        
        for instance in pending_inspection:
            days_in_inspection = (datetime.utcnow() - instance.updated_at).days
            
            if days_in_inspection > 3:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
            
            alert = self.create_alert(
                alert_type=AlertType.INSPECTION_PENDING,
                severity=severity,
                title=f"Material Pending Inspection",
                message=f"Material instance {instance.barcode or instance.id} has been in inspection for {days_in_inspection} day(s)",
                entity_type="material_instance",
                entity_id=instance.id,
                entity_reference=instance.barcode,
                data={
                    "material_id": instance.material_id,
                    "days_in_inspection": days_in_inspection,
                    "quantity": float(instance.quantity)
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def get_all_alerts(self, db: Session, filter_params: Optional[AlertFilter] = None) -> AlertSummary:
        """Get all active alerts."""
        all_alerts: List[Alert] = []
        
        # Collect all alerts
        all_alerts.extend(self.get_po_pending_approval_alerts(db))
        all_alerts.extend(self.get_quantity_mismatch_alerts(db))
        all_alerts.extend(self.get_delayed_delivery_alerts(db))
        all_alerts.extend(self.get_low_stock_alerts(db))
        all_alerts.extend(self.get_fast_moving_material_alerts(db))
        all_alerts.extend(self.get_inspection_pending_alerts(db))
        
        # Apply filters if provided
        if filter_params:
            if filter_params.types:
                all_alerts = [a for a in all_alerts if a.type in filter_params.types]
            if filter_params.severities:
                all_alerts = [a for a in all_alerts if a.severity in filter_params.severities]
            if filter_params.entity_type:
                all_alerts = [a for a in all_alerts if a.entity_type == filter_params.entity_type]
            if filter_params.acknowledged is not None:
                all_alerts = [a for a in all_alerts if a.acknowledged == filter_params.acknowledged]
        
        # Sort by severity and date
        severity_order = {AlertSeverity.CRITICAL: 0, AlertSeverity.WARNING: 1, AlertSeverity.INFO: 2}
        all_alerts.sort(key=lambda x: (severity_order[x.severity], x.created_at), reverse=True)
        
        # Create summary
        return AlertSummary(
            total_alerts=len(all_alerts),
            critical_count=sum(1 for a in all_alerts if a.severity == AlertSeverity.CRITICAL),
            warning_count=sum(1 for a in all_alerts if a.severity == AlertSeverity.WARNING),
            info_count=sum(1 for a in all_alerts if a.severity == AlertSeverity.INFO),
            po_pending_approvals=sum(1 for a in all_alerts if a.type == AlertType.PO_PENDING_APPROVAL),
            quantity_mismatches=sum(1 for a in all_alerts if a.type == AlertType.QUANTITY_MISMATCH),
            delayed_deliveries=sum(1 for a in all_alerts if a.type == AlertType.DELAYED_DELIVERY),
            low_stock_items=sum(1 for a in all_alerts if a.type == AlertType.LOW_STOCK),
            alerts=all_alerts
        )
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        if alert_id in self._alerts_cache:
            alert = self._alerts_cache[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            return alert
        return None


# Singleton instance
alert_service = AlertService()
