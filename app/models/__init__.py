"""SQLAlchemy models for aerospace parts material management."""
# Base
from app.models.base import TimestampMixin

# User and authentication
from app.models.user import User, UserRole, Department

# Materials
from app.models.material import Material, MaterialCategory, MaterialType, MaterialStatus

# Parts
from app.models.part import Part, PartMaterial, PartStatus, PartCriticality

# Suppliers
from app.models.supplier import Supplier, SupplierMaterial, SupplierStatus, SupplierTier

# Inventory
from app.models.inventory import Inventory, InventoryTransaction, InventoryStatus, TransactionType

# Certifications
from app.models.certification import Certification, MaterialCertification, CertificationType, CertificationStatus

# Orders
from app.models.order import Order, OrderItem, OrderStatus, OrderPriority

# Barcode tracking
from app.models.barcode import BarcodeLabel, BarcodeScanLog, BarcodeType, BarcodeStatus

# Workflow and approvals
from app.models.workflow import (
    WorkflowTemplate, WorkflowStep, WorkflowInstance, WorkflowApproval,
    WorkflowType, WorkflowStatus, ApprovalStatus
)

# Projects and BOM
from app.models.project import (
    Project, BillOfMaterials, BOMItem, MaterialRequisition, MaterialRequisitionItem,
    ProjectStatus, ProjectPriority, BOMStatus, BOMType
)

# Audit
from app.models.audit import AuditLog, DataChangeLog, LoginHistory, AuditAction

__all__ = [
    # Base
    "TimestampMixin",
    # User
    "User", "UserRole", "Department",
    # Material
    "Material", "MaterialCategory", "MaterialType", "MaterialStatus",
    # Part
    "Part", "PartMaterial", "PartStatus", "PartCriticality",
    # Supplier
    "Supplier", "SupplierMaterial", "SupplierStatus", "SupplierTier",
    # Inventory
    "Inventory", "InventoryTransaction", "InventoryStatus", "TransactionType",
    # Certification
    "Certification", "MaterialCertification", "CertificationType", "CertificationStatus",
    # Order
    "Order", "OrderItem", "OrderStatus", "OrderPriority",
    # Barcode
    "BarcodeLabel", "BarcodeScanLog", "BarcodeType", "BarcodeStatus",
    # Workflow
    "WorkflowTemplate", "WorkflowStep", "WorkflowInstance", "WorkflowApproval",
    "WorkflowType", "WorkflowStatus", "ApprovalStatus",
    # Project and BOM
    "Project", "BillOfMaterials", "BOMItem", "MaterialRequisition", "MaterialRequisitionItem",
    "ProjectStatus", "ProjectPriority", "BOMStatus", "BOMType",
    # Audit
    "AuditLog", "DataChangeLog", "LoginHistory", "AuditAction",
]
