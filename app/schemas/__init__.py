"""Pydantic schemas for request/response validation."""
# User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    Token, TokenPayload, UserRole, Department
)

# Material
from app.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    MaterialCategoryCreate, MaterialCategoryUpdate, MaterialCategoryResponse,
    MaterialType, MaterialStatus
)

# Part
from app.schemas.part import (
    PartCreate, PartUpdate, PartResponse,
    PartMaterialCreate, PartMaterialUpdate, PartMaterialResponse,
    PartStatus, PartCriticality
)

# Supplier
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    SupplierMaterialCreate, SupplierMaterialUpdate, SupplierMaterialResponse,
    SupplierStatus, SupplierTier
)

# Inventory
from app.schemas.inventory import (
    InventoryCreate, InventoryUpdate, InventoryResponse,
    InventoryTransactionCreate, InventoryTransactionResponse,
    InventoryStatus, TransactionType
)

# Certification
from app.schemas.certification import (
    CertificationCreate, CertificationUpdate, CertificationResponse,
    MaterialCertificationCreate, MaterialCertificationUpdate, MaterialCertificationResponse,
    CertificationType, CertificationStatus
)

# Order
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse,
    OrderItemCreate, OrderItemUpdate, OrderItemResponse,
    OrderStatus, OrderPriority
)

# Barcode
from app.schemas.barcode import (
    BarcodeLabelCreate, BarcodeLabelUpdate, BarcodeLabelResponse,
    BarcodeScanLogCreate, BarcodeScanLogResponse,
    BarcodeType, BarcodeStatus
)

# Workflow
from app.schemas.workflow import (
    WorkflowTemplateCreate, WorkflowTemplateUpdate, WorkflowTemplateResponse,
    WorkflowStepCreate, WorkflowStepUpdate, WorkflowStepResponse,
    WorkflowInstanceCreate, WorkflowInstanceUpdate, WorkflowInstanceResponse,
    WorkflowApprovalAction, WorkflowApprovalResponse,
    WorkflowType, WorkflowStatus, ApprovalStatus
)

# Project and BOM
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    BOMCreate, BOMUpdate, BOMResponse,
    BOMItemCreate, BOMItemUpdate, BOMItemResponse,
    MaterialRequisitionCreate, MaterialRequisitionUpdate, MaterialRequisitionResponse,
    MaterialRequisitionItemCreate, MaterialRequisitionItemUpdate, MaterialRequisitionItemResponse,
    ProjectStatus, ProjectPriority, BOMStatus, BOMType
)

# Audit
from app.schemas.audit import (
    AuditLogCreate, AuditLogResponse,
    DataChangeLogResponse, LoginHistoryResponse,
    AuditLogQuery, AuditAction
)

# Purchase Order (Enhanced)
from app.schemas.purchase_order import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, PurchaseOrderListResponse,
    POLineItemCreate, POLineItemUpdate, POLineItemResponse,
    POApprovalRequest, POApprovalHistoryResponse,
    GoodsReceiptNoteCreate, GoodsReceiptNoteUpdate, GoodsReceiptNoteResponse,
    GRNLineItemCreate, GRNLineItemUpdate, GRNLineItemResponse,
    MaterialLifecycleUpdate, MaterialLifecycleTracker, POSummary, SupplierPOSummary,
    POStatusEnum, POPriorityEnum, MaterialStageEnum, GRNStatusEnum, ApprovalActionEnum
)

# Common
from app.schemas.common import PaginatedResponse, Message

__all__ = [
    # User
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload", "UserRole", "Department",
    # Material
    "MaterialCreate", "MaterialUpdate", "MaterialResponse",
    "MaterialCategoryCreate", "MaterialCategoryUpdate", "MaterialCategoryResponse",
    "MaterialType", "MaterialStatus",
    # Part
    "PartCreate", "PartUpdate", "PartResponse",
    "PartMaterialCreate", "PartMaterialUpdate", "PartMaterialResponse",
    "PartStatus", "PartCriticality",
    # Supplier
    "SupplierCreate", "SupplierUpdate", "SupplierResponse",
    "SupplierMaterialCreate", "SupplierMaterialUpdate", "SupplierMaterialResponse",
    "SupplierStatus", "SupplierTier",
    # Inventory
    "InventoryCreate", "InventoryUpdate", "InventoryResponse",
    "InventoryTransactionCreate", "InventoryTransactionResponse",
    "InventoryStatus", "TransactionType",
    # Certification
    "CertificationCreate", "CertificationUpdate", "CertificationResponse",
    "MaterialCertificationCreate", "MaterialCertificationUpdate", "MaterialCertificationResponse",
    "CertificationType", "CertificationStatus",
    # Order
    "OrderCreate", "OrderUpdate", "OrderResponse",
    "OrderItemCreate", "OrderItemUpdate", "OrderItemResponse",
    "OrderStatus", "OrderPriority",
    # Barcode
    "BarcodeLabelCreate", "BarcodeLabelUpdate", "BarcodeLabelResponse",
    "BarcodeScanLogCreate", "BarcodeScanLogResponse",
    "BarcodeType", "BarcodeStatus",
    # Workflow
    "WorkflowTemplateCreate", "WorkflowTemplateUpdate", "WorkflowTemplateResponse",
    "WorkflowStepCreate", "WorkflowStepUpdate", "WorkflowStepResponse",
    "WorkflowInstanceCreate", "WorkflowInstanceUpdate", "WorkflowInstanceResponse",
    "WorkflowApprovalAction", "WorkflowApprovalResponse",
    "WorkflowType", "WorkflowStatus", "ApprovalStatus",
    # Project and BOM
    "ProjectCreate", "ProjectUpdate", "ProjectResponse",
    "BOMCreate", "BOMUpdate", "BOMResponse",
    "BOMItemCreate", "BOMItemUpdate", "BOMItemResponse",
    "MaterialRequisitionCreate", "MaterialRequisitionUpdate", "MaterialRequisitionResponse",
    "MaterialRequisitionItemCreate", "MaterialRequisitionItemUpdate", "MaterialRequisitionItemResponse",
    "ProjectStatus", "ProjectPriority", "BOMStatus", "BOMType",
    # Audit
    "AuditLogCreate", "AuditLogResponse",
    "DataChangeLogResponse", "LoginHistoryResponse",
    "AuditLogQuery", "AuditAction",
    # Purchase Order (Enhanced)
    "PurchaseOrderCreate", "PurchaseOrderUpdate", "PurchaseOrderResponse", "PurchaseOrderListResponse",
    "POLineItemCreate", "POLineItemUpdate", "POLineItemResponse",
    "POApprovalRequest", "POApprovalHistoryResponse",
    "GoodsReceiptNoteCreate", "GoodsReceiptNoteUpdate", "GoodsReceiptNoteResponse",
    "GRNLineItemCreate", "GRNLineItemUpdate", "GRNLineItemResponse",
    "MaterialLifecycleUpdate", "MaterialLifecycleTracker", "POSummary", "SupplierPOSummary",
    "POStatusEnum", "POPriorityEnum", "MaterialStageEnum", "GRNStatusEnum", "ApprovalActionEnum",
    # Common
    "PaginatedResponse", "Message",
]
