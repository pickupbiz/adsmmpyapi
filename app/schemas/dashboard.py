"""
Dashboard and reporting schemas.

Provides schemas for:
- Real-time PO status dashboard
- Material status with PO tracking
- Supplier performance analytics
- Alerts and notifications
- Report data structures
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class AlertType(str, Enum):
    """Types of alerts."""
    PO_PENDING_APPROVAL = "po_pending_approval"
    QUANTITY_MISMATCH = "quantity_mismatch"
    DELAYED_DELIVERY = "delayed_delivery"
    FAST_MOVING_MATERIAL = "fast_moving_material"
    LOW_STOCK = "low_stock"
    PO_OVERDUE = "po_overdue"
    INSPECTION_PENDING = "inspection_pending"
    APPROVAL_OVERDUE = "approval_overdue"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ReportFormat(str, Enum):
    """Export format options."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class DateRange(str, Enum):
    """Predefined date ranges."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


# =============================================================================
# Dashboard Summary Schemas
# =============================================================================

class POStatusCount(BaseModel):
    """Count of POs by status."""
    status: str
    count: int
    total_value: Decimal = Decimal("0.00")


class PODashboardSummary(BaseModel):
    """Summary of PO statistics for dashboard."""
    total_pos: int = 0
    draft_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    ordered_count: int = 0
    partially_received_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    
    total_value: Decimal = Decimal("0.00")
    pending_value: Decimal = Decimal("0.00")
    ordered_value: Decimal = Decimal("0.00")
    received_value: Decimal = Decimal("0.00")
    
    pos_by_status: List[POStatusCount] = []
    avg_approval_time_hours: Optional[float] = None
    avg_delivery_time_days: Optional[float] = None
    
    overdue_pos: int = 0
    pos_pending_this_week: int = 0


class MaterialStatusCount(BaseModel):
    """Count of materials by lifecycle status."""
    status: str
    count: int
    total_quantity: Decimal = Decimal("0.00")


class MaterialDashboardSummary(BaseModel):
    """Summary of material statistics for dashboard."""
    total_material_instances: int = 0
    ordered_count: int = 0
    received_count: int = 0
    in_inspection_count: int = 0
    in_storage_count: int = 0
    issued_count: int = 0
    in_production_count: int = 0
    completed_count: int = 0
    rejected_count: int = 0
    
    materials_by_status: List[MaterialStatusCount] = []
    
    pending_inspection: int = 0
    low_stock_items: int = 0
    expiring_soon: int = 0
    
    total_inventory_value: Decimal = Decimal("0.00")


class InventoryStatusSummary(BaseModel):
    """Inventory status summary."""
    total_items: int = 0
    total_quantity: Decimal = Decimal("0.00")
    total_value: Decimal = Decimal("0.00")
    low_stock_items: int = 0
    out_of_stock_items: int = 0
    items_below_reorder: int = 0


class DashboardOverview(BaseModel):
    """Complete dashboard overview."""
    po_summary: PODashboardSummary
    material_summary: MaterialDashboardSummary
    inventory_summary: InventoryStatusSummary
    recent_alerts: List["Alert"] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PO Analytics Schemas
# =============================================================================

class POVsReceivedComparison(BaseModel):
    """Comparison of PO ordered vs received quantities."""
    po_id: int
    po_number: str
    supplier_name: str
    line_items: List["POLineComparison"] = []
    total_ordered_quantity: Decimal = Decimal("0.00")
    total_received_quantity: Decimal = Decimal("0.00")
    variance_percentage: float = 0.0
    status: str
    has_mismatch: bool = False


class POLineComparison(BaseModel):
    """Line item comparison for PO vs received."""
    material_id: int
    material_name: str
    ordered_quantity: Decimal
    received_quantity: Decimal
    unit: str
    variance: Decimal
    variance_percentage: float
    status: str


class PODeliveryAnalytics(BaseModel):
    """PO delivery performance analytics."""
    total_pos_analyzed: int = 0
    on_time_deliveries: int = 0
    late_deliveries: int = 0
    early_deliveries: int = 0
    on_time_percentage: float = 0.0
    avg_delay_days: float = 0.0
    max_delay_days: int = 0


class POToProductionLeadTime(BaseModel):
    """Lead time analytics from PO to production."""
    material_id: int
    material_name: str
    avg_po_to_receipt_days: float = 0.0
    avg_receipt_to_inspection_days: float = 0.0
    avg_inspection_to_storage_days: float = 0.0
    avg_storage_to_issue_days: float = 0.0
    avg_issue_to_production_days: float = 0.0
    total_lead_time_days: float = 0.0
    sample_size: int = 0


class LeadTimeReport(BaseModel):
    """Complete lead time report."""
    report_period: str
    generated_at: datetime
    overall_avg_lead_time_days: float = 0.0
    materials: List[POToProductionLeadTime] = []
    bottlenecks: List[str] = []


# =============================================================================
# Supplier Analytics Schemas
# =============================================================================

class SupplierPerformanceMetrics(BaseModel):
    """Performance metrics for a single supplier."""
    supplier_id: int
    supplier_name: str
    supplier_code: str
    
    total_pos: int = 0
    completed_pos: int = 0
    cancelled_pos: int = 0
    
    total_value: Decimal = Decimal("0.00")
    
    on_time_delivery_rate: float = 0.0
    quality_acceptance_rate: float = 0.0
    quantity_accuracy_rate: float = 0.0
    
    avg_delivery_time_days: float = 0.0
    avg_price_variance: float = 0.0
    
    defect_rate: float = 0.0
    return_rate: float = 0.0
    
    performance_score: float = 0.0  # Weighted composite score
    performance_trend: str = "stable"  # improving, declining, stable
    
    last_po_date: Optional[datetime] = None


class SupplierRanking(BaseModel):
    """Supplier ranking data."""
    rank: int
    supplier_id: int
    supplier_name: str
    score: float
    metrics: SupplierPerformanceMetrics


class SupplierAnalyticsReport(BaseModel):
    """Complete supplier analytics report."""
    report_period: str
    generated_at: datetime
    total_suppliers: int = 0
    active_suppliers: int = 0
    top_performers: List[SupplierRanking] = []
    underperformers: List[SupplierRanking] = []
    supplier_metrics: List[SupplierPerformanceMetrics] = []


# =============================================================================
# Project & Consumption Reports
# =============================================================================

class ProjectPOConsumption(BaseModel):
    """PO consumption data for a project."""
    project_id: int
    project_name: str
    project_code: str
    
    total_pos_linked: int = 0
    total_po_value: Decimal = Decimal("0.00")
    materials_consumed: List["MaterialConsumptionItem"] = []
    
    budget_allocated: Decimal = Decimal("0.00")
    budget_utilized: Decimal = Decimal("0.00")
    budget_remaining: Decimal = Decimal("0.00")
    utilization_percentage: float = 0.0


class MaterialConsumptionItem(BaseModel):
    """Individual material consumption details."""
    material_id: int
    material_name: str
    po_number: str
    ordered_quantity: Decimal
    consumed_quantity: Decimal
    remaining_quantity: Decimal
    unit: str
    unit_price: Decimal
    total_cost: Decimal


class ProjectConsumptionReport(BaseModel):
    """Complete project consumption report."""
    report_period: str
    generated_at: datetime
    projects: List[ProjectPOConsumption] = []
    total_consumption_value: Decimal = Decimal("0.00")


# =============================================================================
# Material Movement & History
# =============================================================================

class MaterialMovementRecord(BaseModel):
    """Single material movement record."""
    id: int
    material_instance_id: int
    material_name: str
    barcode: Optional[str] = None
    
    from_status: str
    to_status: str
    quantity: Decimal
    unit: str
    
    po_number: Optional[str] = None
    po_id: Optional[int] = None
    grn_number: Optional[str] = None
    
    project_name: Optional[str] = None
    location: Optional[str] = None
    
    performed_by: str
    performed_at: datetime
    notes: Optional[str] = None


class MaterialMovementHistory(BaseModel):
    """Material movement history report."""
    material_id: Optional[int] = None
    material_name: Optional[str] = None
    total_movements: int = 0
    movements: List[MaterialMovementRecord] = []
    date_range: str


# =============================================================================
# Alerts
# =============================================================================

class Alert(BaseModel):
    """Alert/notification data."""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    
    entity_type: Optional[str] = None  # po, material, inventory, etc.
    entity_id: Optional[int] = None
    entity_reference: Optional[str] = None
    
    data: Optional[Dict[str, Any]] = None
    
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertSummary(BaseModel):
    """Summary of active alerts."""
    total_alerts: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    
    po_pending_approvals: int = 0
    quantity_mismatches: int = 0
    delayed_deliveries: int = 0
    low_stock_items: int = 0
    
    alerts: List[Alert] = []


class AlertFilter(BaseModel):
    """Filter criteria for alerts."""
    types: Optional[List[AlertType]] = None
    severities: Optional[List[AlertSeverity]] = None
    entity_type: Optional[str] = None
    acknowledged: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


# =============================================================================
# Report Request/Response Schemas
# =============================================================================

class ReportRequest(BaseModel):
    """Base report request."""
    date_range: DateRange = DateRange.LAST_30_DAYS
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: ReportFormat = ReportFormat.PDF


class POReportRequest(ReportRequest):
    """PO-specific report request."""
    supplier_ids: Optional[List[int]] = None
    status_filter: Optional[List[str]] = None
    include_line_items: bool = True


class MaterialReportRequest(ReportRequest):
    """Material-specific report request."""
    material_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None
    status_filter: Optional[List[str]] = None


class ProjectReportRequest(ReportRequest):
    """Project-specific report request."""
    project_ids: Optional[List[int]] = None
    include_bom_details: bool = True


class SupplierReportRequest(ReportRequest):
    """Supplier-specific report request."""
    supplier_ids: Optional[List[int]] = None
    min_po_count: int = 1


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: str
    report_name: str
    format: ReportFormat
    generated_at: datetime
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    expires_at: Optional[datetime] = None


# =============================================================================
# WebSocket Message Schemas
# =============================================================================

class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    PO_STATUS_CHANGE = "po_status_change"
    MATERIAL_STATUS_CHANGE = "material_status_change"
    NEW_ALERT = "new_alert"
    INVENTORY_UPDATE = "inventory_update"
    APPROVAL_REQUIRED = "approval_required"
    DASHBOARD_UPDATE = "dashboard_update"
    GRN_RECEIVED = "grn_received"
    INSPECTION_COMPLETE = "inspection_complete"


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: WebSocketMessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


# =============================================================================
# Fast-Moving & Stock Analysis
# =============================================================================

class FastMovingMaterial(BaseModel):
    """Fast-moving material analysis."""
    material_id: int
    material_name: str
    material_code: str
    
    consumption_rate: Decimal  # Units per day
    total_consumed_30_days: Decimal
    total_consumed_90_days: Decimal
    
    avg_po_quantity: Decimal
    po_frequency: int  # POs per month
    
    current_stock: Decimal
    days_of_stock: float
    recommended_reorder_qty: Decimal


class LowStockItem(BaseModel):
    """Low stock item details."""
    material_id: int
    material_name: str
    material_code: str
    
    current_stock: Decimal
    minimum_stock: Decimal
    reorder_level: Decimal
    unit: str
    
    stock_percentage: float  # Current vs minimum
    days_until_stockout: Optional[float] = None
    
    pending_po_quantity: Decimal = Decimal("0.00")
    expected_delivery_date: Optional[date] = None
    
    last_po_date: Optional[date] = None
    avg_consumption_rate: Decimal = Decimal("0.00")


class StockAnalysisReport(BaseModel):
    """Complete stock analysis report."""
    generated_at: datetime
    fast_moving_materials: List[FastMovingMaterial] = []
    low_stock_items: List[LowStockItem] = []
    out_of_stock_items: List[LowStockItem] = []
    critical_items: List[LowStockItem] = []  # Below minimum
    items_with_pending_pos: int = 0


# Update forward references
POVsReceivedComparison.model_rebuild()
ProjectPOConsumption.model_rebuild()
DashboardOverview.model_rebuild()
